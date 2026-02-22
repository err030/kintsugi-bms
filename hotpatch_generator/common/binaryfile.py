from elftools.elf.elffile import ELFFile, Section, RelocationSection

class Relocation:

    def __init__(self, target_section_index, target_code_offset, name) -> None:
        self.target_section_index = target_section_index
        self.target_code_offset = target_code_offset
        self.name = name

class BinaryFile:

    def __init__(self) -> None:
        self.file_handle = None
        self.elf_handle = None
        self.relocation_table = dict()

    def _load_relocation_table(self):

        if self.elf_handle is None:
            # print("[error]: cannot load relocation table because there is no elf file open")
            return
        
        self.relocation_table = dict()
        
        symbol_table = self.get_symbol_table()

        for relocation_section in self.elf_handle.iter_sections():
            if not isinstance(relocation_section, RelocationSection):
                continue

            relocation_section_name = relocation_section.name.rsplit(".")[-1]
            relocation_target_section = self.elf_handle.get_section_by_name(".text." + relocation_section_name)

            if relocation_target_section is None:
                continue

            if relocation_section_name not in self.relocation_table:
                self.relocation_table[relocation_section_name] = list()
            
            for relocation in relocation_section.iter_relocations():
                relocation_symbol = symbol_table.get_symbol(relocation["r_info_sym"])
                relocation_offset = relocation["r_offset"]
                relocation_target_section_index = self.get_section_index(relocation_target_section)
                relocation_entry = Relocation(relocation_target_section_index, relocation_offset, relocation_symbol.name)

                self.relocation_table[relocation_section_name].append(relocation_entry)

    def load(self, filename) -> bool:
        self.file_handle = open(filename, "rb")

        if self.file_handle is None:
            print(f"[error]: could not open file '{filename}'")
            return False
        
        self.elf_handle = ELFFile(self.file_handle)

        if self.elf_handle is None:
            print(f"[error]: could not open file as elf file '{filename}'")
            return False
        
        self._load_relocation_table()
        
        return True
    
    def read_bytes(self, offset : int, length : int) -> bytearray:
        prev_offset = self.file_handle.tell()
        self.file_handle.seek(offset, 0)
        data = self.file_handle.read(length)
        self.file_handle.seek(prev_offset, 0)
        return data
    
    def read_bytes_from_section(self, section : Section, address : int, length : int) -> bytearray:
        if address >= section["sh_addr"] and address < section["sh_addr"] + section["sh_size"]:
            data = self.get_section_data(section)

            offset = address - section["sh_addr"]
            return data[offset : offset + length]
        return None
        
    
    def get_segments(self) -> list:
        if self.elf_handle is None:
            print("[error]: cannot get segments because there is no elf file open")
            return []
        
        return [ section for section in self.elf_handle.iter_segments() ]
    
    def get_section_distribution(self, section) -> list:
        if self.elf_handle is None:
            print("[error]: cannot get section distribution because there is no elf file open")
            return []
        
        symbol_table = self.elf_handle.get_section_by_name(".symtab")
        section_index = self.elf_handle.get_section_index(section.name)

        distribution = list()
        for symbol in symbol_table.iter_symbols():
            if symbol.entry["st_shndx"] == section_index:
                if symbol.name not in [ "$a", "$t", "$d"]:
                    continue
                distribution.append({
                    "start" : symbol["st_value"],
                    "type" : symbol.name
                    })

        return distribution
    
    def get_section_symbols(self, section):
        if self.elf_handle is None:
            print("[error]: cannot get section symbols because there is no elf file open")
            return []
        
        symbol_table = self.elf_handle.get_section_by_name(".symtab")
        section_index = self.elf_handle.get_section_index(section.name)

        symbols = list()
        for symbol in symbol_table.iter_symbols():
            if symbol.entry["st_shndx"] == section_index:
                symbols.append({
                    "name"   : symbol.name,
                    "value"  : symbol.entry["st_value"]
                })
        
        return symbols
    
    def get_symbol_from_section(self, section, symbol_name):
        symbols = self.get_section_symbols(section)

        for symbol in symbols:
            if symbol_name in symbol["name"]:
                return symbol
        
        return None
    
    def get_symbol_table(self):
        return self.elf_handle.get_section_by_name(".symtab")

    def get_symbol_from_name(self, name : str):
        symbol_table = self.get_symbol_table()

        if symbol_table is None:
            return None
    
        for symbol in symbol_table.iter_symbols():
            if name == symbol.name:
                return symbol
            
        return None
    
    def get_symbols_with_prefix(self, name : str):
        symbol_table = self.get_symbol_table()

        if symbol_table is None:
            return None
    
        result = list()
        for symbol in symbol_table.iter_symbols():
            if symbol.name[:len(name)] == name:
                result.append(symbol)
            
        return result
    
    def get_section_from_symbol(self, symbol):
        address = symbol["st_value"]

        for section in self.get_sections():
            if address >= section["sh_addr"] and address < section["sh_addr"] + section["sh_size"]:
                return section
        return None

    def get_sections(self) -> list:
        if self.elf_handle is None:
            print("[error]: cannot get sections because there is no elf file open")
            return []
        
        return [ section for section in self.elf_handle.iter_sections() ]
    
    def get_relocation_call(self, section, offset):
        if self.elf_handle is None:
            print("[error]: cannot get relocation call because there is no elf file open")
            return None
        
        section_name = section.name.rsplit(".")[-1]

        if section_name in self.relocation_table:
            relocation_table = self.relocation_table[section_name]

            for relocation in relocation_table:
                if offset == relocation.target_code_offset:
                    return relocation
            
        return None

    def get_relocation_sections(self) -> list:
        if self.elf_handle is None:
            print("[error]: cannot get relocation sections because there is no elf file open")
            return []

        sections = list()
        for section in self.elf_handle.iter_sections():
            if section.header.sh_type in [ "SHT_REL", "SHT_RELA" ] and section.header.sh_flags & 0x40 == 0x40:
                sections.append(section)
        
        return sections
    
    def get_relocations(self):
        relocations = list()
        symbol_table = self.get_symbol_table()
        for section in self.get_relocation_sections():
            if ".text" not in section.name:
                continue

            for relocation in section.iter_relocations():
                symbol = symbol_table.get_symbol(relocation["r_info_sym"])
                section_index = symbol.entry["st_shndx"]
                
                symbol_section = None
                if section_index != "SHN_UNDEF" and section_index != "SHN_ABS":
                    # print(section_index)
                    symbol_section = self.elf_handle.get_section(section_index)

                offset = relocation["r_offset"]
                relocations.append({
                    "symbol" : symbol,
                    "section_index" : section_index,
                    "symbol_section" : symbol_section,
                    "offset" : offset
                })

        return relocations
    
    def get_relocations_with_prefix(self, prefix : str):
        relocations = self.get_relocations()

        result = list()
        for relocation in relocations:
            if relocation["symbol"].name[:len(prefix)] == prefix:
                result.append(relocation)
        
        return result
    
    def get_relocation_with_name(self, name : str):
        relocations = self.get_relocations()

        for relocation in relocations:
            if name in relocation["symbol"].name:
                return relocation
            if relocation["symbol_section"] is not None and name in relocation["symbol_section"].name:
                return relocation
        
        return None

    def get_executable_sections(self) -> list:
        if self.elf_handle is None:
            print("[error]: cannot get executable sections because there is no elf file open")
            return []

        sections = list()
        for section in self.elf_handle.iter_sections():
            if section.header.sh_type == "SHT_PROGBITS" and (section.header.sh_flags & 4) == 4:
                sections.append(section)
        
        return sections
    
    def get_executable_sections_with_prefix(self, prefix : str):
        sections = list()

        for section in self.get_executable_sections():
            if section.name[:len(prefix)] == prefix:
                sections.append(section)
        
        return sections
    
    def get_section_by_index(self, index) -> Section:
        if self.elf_handle is None:
            print("[error]: cannot get section by index because there is no elf file open")
            return None
        
        count = 0
        for section in self.elf_handle.iter_sections():
            if count == index:
                return section
            count += 1
        
        return None
    
    def get_section_index(self, section) -> Section:
        return self.elf_handle.get_section_index(section.name)

    def get_section_data(self, section : Section) -> bytes:
        offset = section.header.sh_offset
        size = section.header.sh_size

        self.file_handle.seek(offset, 0)
        data = self.file_handle.read(size)

        return data

