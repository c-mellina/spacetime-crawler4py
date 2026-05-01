class ExactDetector(object):
    def __init__(self):
        self.checkSum_set = {}
    
    def is_exact_duplicate(self, words):
        checkSum = 0
        for word in words:
            for char in word:
                checkSum += ord(char)
        
        if not checkSum in self.checkSum_set:
            self.checkSum_set.add(checkSum)
            return False
        else:
            return True





class NearDetector(object):
    def __init__(self):
        self.fingerprint_set = {}
    
    def is_near_duplicate(self, words):
        return False    # Not working yet lol