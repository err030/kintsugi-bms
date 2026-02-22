
from common.objectfile import ObjectFile

class HotpatchFile:

    def __init__(self) -> None:
        self.object_file = None

    def load(self, filename) -> bool:
        object_file = ObjectFile()

        if not object_file.load(filename):
            return False

        self.object_file = object_file
        return True 
    
    def get_hotpatch_information(self, name, offset, orig_path, zephyr_path):
        assert self.object_file is not None

        orig_file = ObjectFile()
        if not orig_file.load(orig_path):
            # print("[error]: could not load original object file")
            return None

        hotpatch_information = dict()

        # find the hotpatch function in the sections
        executable_sections = self.object_file.get_executable_sections()
        hotpatch_section = None
        for section in executable_sections:
            if "hotpatch_function" in section.name:
                hotpatch_section = section
                break

        if hotpatch_section is None:
            # print("[error]: could not find hotpatch funtion section")
            return None
        
        # get the original code symbol
        original_code_symbol = self.object_file.get_symbol_from_section(hotpatch_section, "hotpatch_original_code")
        if original_code_symbol is None:
            # print("[error]: there is no original code label in the hopatching code")
            return None
        
        hotpatch_information["original_code"] = original_code_symbol
        
        # get the return address relocations
        hotpatch_information["return_addresses"] = list()

        return_relocations = self.object_file.get_relocations_with_prefix("hotpatch_function_return_")
        for relocation in return_relocations:
            hotpatch_information["return_addresses"].append(relocation)    

        # TODO: get the function calls

        # get the data of the patch
        patch_data = self.object_file.get_section_data(section)

        
        # get the original functions code
        orig_executable_sections = orig_file.get_executable_sections()
        orig_code_section = None 
        for orig_section in orig_executable_sections:
            if name in orig_section.name:
                orig_code_section = orig_section
                break
        
        if orig_code_section is None:
            # print("[error]: could not find original code section")
            return None
        
        # get the original code data
        orig_code_data = orig_file.get_section_data(orig_code_section)
        if orig_code_data is None:
            # print("[error]: could not get original code data")
            return None
        
        original_code = orig_code_data[offset:offset+4]

        # overwrite the original code label in the patch
        orig_offset = original_code_symbol["value"]
        patch_data = patch_data[:orig_offset] + original_code + patch_data[orig_offset + len(original_code):]

        zephyr_file = ObjectFile()
        if not zephyr_file.load(zephyr_path):
            # print("[error]: could not load zephyr elf")
            return None
        
        zephyr_symbol_table = zephyr_file.get_symbol_table()
        orig_symbol = None
        for symbol in zephyr_symbol_table.iter_symbols():
            if symbol.name == name:
                orig_symbol = symbol
                break

        