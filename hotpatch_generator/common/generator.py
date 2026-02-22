import struct
from common.binaryfile import BinaryFile

class HotpatchGenerator:

    def __init__(self, patch_object_file : BinaryFile, firmware_elf_file : BinaryFile) -> None:
        assert patch_object_file is not None and firmware_elf_file is not None

        self.patch_object_file = patch_object_file
        self.firmware_elf_file = firmware_elf_file

    def _get_string_between(self, source, start, end):
        start_index = source.find(start)
        if start_index == -1:
            return ""
        end_index = source.find(end, start_index + len(start))
        if end_index == -1:
            return ""
        return source[start_index + len(start):end_index]

    def _analyze_patch_object_file(self):
        assert self.patch_object_file is not None
        hotpatch_function_information = list()
        for section in self.patch_object_file.get_executable_sections_with_prefix(".text.hotpatch_function"):

            function_name = None
            function_type = None
            function_offset = None
            function_address = None
            function_return_offset = None

            section_name = section.name.rsplit(".text.")[-1]

            offset_string = self._get_string_between(section_name, "_hotpatch_offset_", "_hotpatch_type_")
            if offset_string != "":
                function_offset = int(offset_string, 16)

            type_string = self._get_string_between(section_name, "_hotpatch_type_", "_hotpatch_return_offset_")
            if type_string != "":
                function_type = type_string

            if function_offset is not None and function_type is not None:
                function_name = self._get_string_between(section_name, "hotpatch_function_", "_hotpatch_offset_")
            else:
                function_name = section_name

            return_string = self._get_string_between(section_name, "_hotpatch_return_offset_", "_hotpatch_end")
            if return_string != "":
                function_return_offset = int(return_string, 16)

            # get the address of the function
            function_symbol = self.firmware_elf_file.get_symbol_from_name(function_name)
            if function_symbol is not None:
                function_address = function_symbol.entry["st_value"] & 0xFFFFFFFE

            # get the relocation information for the hotpatch addresses and calls
            hotpatch_address_relocations = list()
            hotpatch_data_relocations = list()
            hotpatch_call_relocations = list()
            hotpatch_back_branch_relocations = list()

            #print("Symbol Sections:")
            for relocation in self.patch_object_file.get_relocations():
                symbol_section = relocation["symbol_section"]
                if symbol_section is not None:
                    #print(symbol_section.name)
                    # get the hotpatch address relocations
                    if ".hotpatch_address_" in symbol_section.name:
                        real_symbol_name = symbol_section.name.rsplit(".bss.hotpatch_address_", 1)[1]
                        hotpatch_address_relocations.append((real_symbol_name, relocation))
                        continue
                    
                    # get the data symbol
                    if ".rodata" in symbol_section.name:
                        hotpatch_data_relocations.append((symbol_section.data(), relocation))
                        continue

                    if ".text." in symbol_section.name:
                        hotpatch_call_relocations.append((relocation["symbol"], relocation))

                symbol = relocation["symbol"]
                if symbol.entry["st_name"] != 0:
                    # get the hotpatch call relocations
                    hotpatch_call_relocations.append((symbol.name, relocation))

            # get the branch to orig symbols
            branch_to_orig_symbols = self.patch_object_file.get_symbols_with_prefix("hotpatch_branch_to_orig")

            # get the function call symbols
            function_call_symbols = self.patch_object_file.get_symbols_with_prefix("hotpatch_external_function_call")

            # get the original code symbol 
            hotpatch_original_code_symbol = self.patch_object_file.get_symbol_from_section(section, "hotpatch_original_code")

            # get the original code bytes
            #print("Function:", function_name)
            elf_symbol = self.firmware_elf_file.get_symbol_from_name(function_name)
            if elf_symbol is None:
                print("[error]: could not find original code function in the ELF binary")
                return None
            
            original_code_section = self.firmware_elf_file.get_section_from_symbol(elf_symbol)
            hotpatch_original_code_bytes = self.firmware_elf_file.read_bytes_from_section(original_code_section, function_address + function_offset, 8)

            # get the code bytes
            hotpatch_code = self.patch_object_file.get_section_data(section)

            # get the return fail relocation
            hotpatch_return_fail_relocation = self.patch_object_file.get_relocation_with_name("hotpatch_address_return_fail")
            hotpatch_function_information.append({
                "function_name"         : function_name,
                "function_address"      : function_address,
                "function_type"         : function_type,
                "patch_offset"          : function_offset,
                "return_offset"         : function_return_offset,
                "address_relocations"   : hotpatch_address_relocations,
                "data_relocations"      : hotpatch_data_relocations,
                "call_relocations"      : hotpatch_call_relocations,
                "original_code_symbol"  : hotpatch_original_code_symbol,
                "original_code_bytes"   : hotpatch_original_code_bytes,
                "branch_to_orig_symbols": branch_to_orig_symbols,
                "return_fail_relocation": hotpatch_return_fail_relocation,
                "code_bytes"            : hotpatch_code,
                "external_calls"        : function_call_symbols
            })

        return hotpatch_function_information
    
    def _align(self, value, alignment):
        """Align the value upwards to the nearest multiple of alignment."""
        if value % alignment == 0:
            return value
        else:
            return value + (alignment - (value % alignment))

    def _resolve_relocations(self, file, relocations : list) -> list:
        resolved_relocations = list()
        unresolved_relocations = list()

        for relocation_name, relocation in relocations:
            # get the symbol from the ELF binary to obtain its real address
            elf_symbol = file.get_symbol_from_name(relocation_name)

            # if the elf symbol is not found, it's a local symbol
            if elf_symbol is None:
                unresolved_relocations.append((relocation_name, relocation))
                continue

            resolved_relocations.append((relocation_name, relocation, elf_symbol))
        
        return resolved_relocations, unresolved_relocations
    
    def replace_bytes(self, data, replace_data, replace_offset) -> bytearray:
        data_prefix = bytearray(data[:replace_offset])
        data_suffix = bytearray([])

        if replace_offset + len(replace_data) < len(data):
            data_suffix = bytearray(data[replace_offset + len(replace_data):])

        return bytearray(data_prefix + replace_data + data_suffix)
    
    def encode_arm_bl(self, source_address, target_address):
        if source_address & 1:
            # Thumb mode
            source_address &= ~1  # Clear Thumb bit
            branch_offset = target_address - (source_address + 8)
            
            # Check if branch offset is within valid range (-16MB to +16MB)
            if not (-16777216 <= branch_offset <= 16777214):
                raise ValueError("Branch offset out of range for Thumb BL instruction")
            
            # Adjust branch offset for encoding
            offset = branch_offset & 0x00FFFFFF  # Mask to 24 bits

            # Extract S, I1, I2
            S = (offset >> 23) & 0x1          # Bit 23
            I1 = (offset >> 22) & 0x1         # Bit 22
            I2 = (offset >> 21) & 0x1         # Bit 21

            # Calculate J1 and J2
            J1 = (~I1 ^ S) & 0x1
            J2 = (~I2 ^ S) & 0x1

            # Extract imm10 and imm11
            imm10 = (offset >> 12) & 0x3FF    # Bits 12-21
            imm11 = (offset >> 1) & 0x7FF     # Bits 1-11

            # Assemble the instruction
            first_halfword = (0b11110 << 11) | (S << 10) | imm10
            second_halfword = (0b11 << 14) | (J1 << 13) | (J2 << 12) | (1 << 11) | imm11

            # Combine the two halfwords into a 32-bit instruction
            encoded_instruction = (second_halfword << 16) | first_halfword

            return encoded_instruction
        else:
            raise NotImplementedError("ARM mode encoding not implemented")

    def generate_hotpatch(self) -> bytes:
        patch_object_information = self._analyze_patch_object_file()

        if patch_object_information is None:
            return None
        
        segment_count = 0
        hotpatch_code_bytes = bytearray()

        for entry in patch_object_information:
            function_name = entry["function_name"]
            function_address  = entry["function_address"]
            patch_offset = entry["patch_offset"]
            return_offset = entry["return_offset"]
            hotpatch_type = 0

            print(f"=> {entry['function_name']} <=")
            call_relocation_count = 0
            call_relocations = bytearray()

            branch_to_orig_count = 0
            branch_to_orig_code = bytearray()
            # get the bytes of the hotpatch code
            code_bytes = bytearray(entry["code_bytes"])

            print("Hotpatch Type:", entry["function_type"])
            if entry["function_type"] == "redirect":
                hotpatch_type = 1

                # replace the bytes of the address relocations
                resolved_address_relocations, _ = self._resolve_relocations(self.firmware_elf_file, entry["address_relocations"])
                for relocation_name, relocation, elf_symbol in resolved_address_relocations:
                    relocation_address = elf_symbol.entry["st_value"]
                    relocation_offset  = relocation["offset"]

                    code_bytes = self.replace_bytes(code_bytes, struct.pack("<I", relocation_address), relocation_offset)

                    print("[Address Relocation]:", relocation_name, "->", hex(relocation_address), hex(relocation_offset))

                # replace the original code bytes
                original_symbol = entry["original_code_symbol"]

                if original_symbol is not None:
                    original_offset = original_symbol["value"]
                    original_bytes  = entry["original_code_bytes"]
                    code_bytes = self.replace_bytes(code_bytes, original_bytes, original_offset)

                print("External Call Offsets")
                external_call_offsets = list()
                for elf_symbol in entry["external_calls"]:
                    call_offset = elf_symbol.entry["st_value"]
                    external_call_offsets.append(call_offset)
                    print("[external call offset]:", hex(call_offset))
                     
                print("Grouping call relocations")
                call_dict = dict()
                resolved_firmware_call_relocations, _ = self._resolve_relocations(self.firmware_elf_file, entry["call_relocations"])
                for relocation_name, relocation, elf_symbol in resolved_firmware_call_relocations:
                    relocation_address = elf_symbol.entry["st_value"]
                    relocation_offset  = relocation["offset"]

                    print("=" * 5, relocation_name,hex(relocation_address), hex(relocation_offset))
                    external_call = False
                    for call_offset in external_call_offsets:
                        if relocation_offset >= call_offset:
                            external_call = True
                            break
                    
                    if relocation_name not in call_dict:
                        call_dict[relocation_name] = { "address" : relocation_address }

                    if external_call == True:
                        call_dict[relocation_name]["external"] = relocation_offset
                    else:
                        call_dict[relocation_name]["local"] = relocation_offset

                for call_name, call_entry in call_dict.items():

                    if "local" not in call_entry or "address" not in call_entry or "external" not in call_entry:
                        print("[error]: missing information for external call")
                        continue

                    call_addr = call_entry["address"]
                    call_offset_local = call_entry["local"]
                    call_offset_external = call_entry["external"]

                    # add encoded branch to the external code
                    encoded_branch = self.encode_arm_bl(call_offset_local | 1, call_offset_external | 1)
                    #code_bytes = self.replace_bytes(code_bytes, struct.pack("<I", relocation_address), relocation_offset)

                    code_bytes = self.replace_bytes(code_bytes, struct.pack("<I", encoded_branch), call_offset_local) 
                
                    # update the load into PC instruction because of potential alignment issues
                    alignment = ((call_offset_external & 0b11)) << 16
                    
                    code_bytes = self.replace_bytes(code_bytes, struct.pack("<I", 0xF000F8DF | alignment), call_offset_external - 4)

                    # update the external address
                    print("Call Addr:", hex(call_addr))
                    code_bytes = self.replace_bytes(code_bytes, struct.pack("<I", call_addr), call_offset_external)

                    print("Patched Call:", call_name)

                print("Call Relocations:")
                print("\t", ", ".join([ call for call, _ in entry["call_relocations"] ]))

                # create the config for the call relocations
                resolved_firmware_call_relocations, _ = self._resolve_relocations(self.firmware_elf_file, entry["call_relocations"])
                for relocation_name, relocation, elf_symbol in resolved_firmware_call_relocations:
                    relocation_address = elf_symbol.entry["st_value"]
                    relocation_offset  = relocation["offset"]
                    print("[Resolved-Call]:", relocation_name, "->", hex(relocation_offset), hex(relocation_address))
                    #call_bytes += struct.pack("<B", 0)
                    call_relocations += struct.pack("<I", relocation_offset)
                    call_relocations += struct.pack("<I", relocation_address)
                    call_relocation_count += 1

                print("Branch to original code:")
                for branch_symbol in entry["branch_to_orig_symbols"]:
                    print(branch_symbol.name, "->", hex(branch_symbol["st_value"]))
                    branch_to_orig_code += struct.pack("<I", branch_symbol["st_value"])
                    alignment = ((branch_symbol["st_value"] & 0b11)) << 16
                    code_bytes = code_bytes[:branch_symbol["st_value"]]+ struct.pack("<II", 0xF000F8DF | alignment, (function_address + patch_offset + return_offset) |1) +code_bytes[branch_symbol["st_value"] + 8:]
                    branch_to_orig_count += 1
                    code_bytes = code_bytes

            elif entry["function_type"]  == "replacement":
                hotpatch_type = 0
                code_bytes = code_bytes[:8]

            segment_format = "<IIII"
            segment_size = struct.calcsize(segment_format)

            hotpatch_data = struct.pack(segment_format,
                                         hotpatch_type,
                                         function_address + patch_offset,
                                         len(code_bytes),
                                         0)
            print(f"Code Offset: {segment_size + call_relocation_count * 8:08X}" )
            print(f"Target Address: {function_address + patch_offset:08X}")
            print(f"Return Offset: {return_offset:02X}")
                                         
            hotpatch_code_bytes += hotpatch_data
            hotpatch_code_bytes += code_bytes

            segment_count += 1

        return hotpatch_code_bytes