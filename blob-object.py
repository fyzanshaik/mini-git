from minigit import MinigitObject

class Blob(MinigitObject):

    def __init__(self, data=None):
        #if the data is a string, we encode it to bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
        super().__init__(data)
        print(f"[Blob] Created blob with {len(self.data)} bytes")

    def get_type(self):
        return "blob"
    #this is a class method that creates a blob object from a file
    @classmethod
    def from_file(cls, file_path):
        print(f"[Blob] Reading file: {file_path}")
        #we open the file in binary mode and read the content "rb flag"
        with open(file_path, 'rb') as f:
            content = f.read()
        print(f"[Blob] Read {len(content)} bytes from {file_path}")
        return cls(content)

    def save_to_file(self, file_path):
        print(f"[Blob] Writing {len(self.data)} bytes to: {file_path}")
        #we open the file in binary mode and write the content "wb flag"
        with open(file_path, 'wb') as f:
            f.write(self.data)
        print(f"[Blob] Successfully wrote file: {file_path}")