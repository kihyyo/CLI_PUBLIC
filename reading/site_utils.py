import re, difflib

class Utils():

    @classmethod
    def remove_special_char(cls, text):
        return re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》：]', '', text)

    @classmethod
    def similar(cls, seq1, seq2):
        return difflib.SequenceMatcher(a=cls.remove_special_char(seq1.lower()), b=cls.remove_special_char(seq2.lower())).ratio()