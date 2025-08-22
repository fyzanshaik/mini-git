import hashlib
import zlib
import os
from abc import ABC, abstractmethod


class MinigitObject(ABC):

    def __init__(self, data=None):
        #This basically initializes the object with the data and sets the hash to None if no data is provided then emotystring
        self.data = data if data is not None else b''
        self.hash = None
        print(f"[MinigitObject] Created {self.__class__.__name__} with {len(self.data)} bytes")
    #An abstract method for inherited classes to implement, just syntactic contract clean code stuff
    @abstractmethod
    def get_type(self):
        pass

    def create_header(self):
        #returns a header string of form <type> <size>\0
        obj_type = self.get_type()
        size = len(self.data)
        header = f"{obj_type} {size}\0".encode('utf-8')
        print(f"[MinigitObject] Created header: '{obj_type} {size}\\0' ({len(header)} bytes)")
        return header

    def get_full_data(self):
        header = self.create_header()
        full_data = header + self.data
        print(f"[MinigitObject] Full data: {len(full_data)} bytes (header: {len(header)}, content: {len(self.data)})")
        return full_data

    def calculate_hash(self):

        full_data = self.get_full_data()
        sha1_hash = hashlib.sha1(full_data).hexdigest()
        self.hash = sha1_hash
        print(f"[MinigitObject] Calculated SHA-1: {sha1_hash}")
        return sha1_hash

    def compress_data(self):

        full_data = self.get_full_data()
        compressed = zlib.compress(full_data)
        print(f"[MinigitObject] Compressed {len(full_data)} bytes -> {len(compressed)} bytes")
        return compressed

    @staticmethod
    def decompress_data(compressed_data):

        decompressed = zlib.decompress(compressed_data)
        print(f"[MinigitObject] Decompressed {len(compressed_data)} bytes -> {len(decompressed)} bytes")
        return decompressed

    @staticmethod
    def parse_object_data(decompressed_data):

        null_index = decompressed_data.find(b'\0')
        if null_index == -1:
            raise ValueError("Invalid object data: no null separator found")

        header = decompressed_data[:null_index].decode('utf-8')
        content = decompressed_data[null_index + 1:]

        header_parts = header.split(' ')
        if len(header_parts) != 2:
            raise ValueError(f"Invalid header format: {header}")

        obj_type = header_parts[0]
        size = int(header_parts[1])

        print(f"[MinigitObject] Parsed object: type={obj_type}, size={size}, content_len={len(content)}")

        if len(content) != size:
            raise ValueError(f"Size mismatch: header says {size}, got {len(content)}")

        return obj_type, size, content

    def get_storage_path_components(self):
        #This is the function that returns the directory and filename for the object, we basically divide the hash in two parts
        if not self.hash:
            self.calculate_hash()

        dir_name = self.hash[:2]
        filename = self.hash[2:]

        print(f"[MinigitObject] Storage path: objects/{dir_name}/{filename}")
        return dir_name, filename



if __name__ == "__main__":
    print("Mini-Git: Use 'python -m unittest discover tests' to run tests")
