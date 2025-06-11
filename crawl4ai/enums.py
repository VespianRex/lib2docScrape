import enum


class URLType(enum.Enum):
    INTERNAL = 1
    EXTERNAL = 2
    UNKNOWN = 3

    def __str__(self):
        return self.name
