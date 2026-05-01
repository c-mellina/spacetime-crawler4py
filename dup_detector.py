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



from collections import Counter
import hashlib

class NearDetector(object):
    def __init__(self, threshold):
        self.fingerprint_list = []
        self.threshold = threshold
    
    def is_near_duplicate(self, words):
        counter = Counter()
        counter.update(words)
        # counter should hopefully hold the words and their frequencies now
        fingerprint = [0] * 256
        for word, count in counter.items():
            # Given word:
                # 1. Hash to bytes
                # 2. Store every bit
                # 3. Iterate through bits, changing fingerprint[i] by +/- count
            bytes = hashlib.sha256(word.encode()).digest()      # https://docs.python.org/3/library/hashlib.html
            bit_list = self.bytes_to_bits(bytes)
            for i in range(len(bit_list)):
                bit = bit_list[i]
                if bit == 0:
                    fingerprint[i] -= count
                else:   # bit == 1
                    fingerprint[i] += count
        
        # We should now have a fingerprint of values
        # Convert to a binary fingerprint
        for i in range(len(fingerprint)):
            if fingerprint[i] > 0:
                fingerprint[i] = 1
            else: # fingerprint[i] <= 0
                fingerprint[i] = 0
        
        for other_fingerprint in self.fingerprint_list:
            similarity = self.compare_fingerprints(fingerprint, other_fingerprint)
            if similarity > self.threshold:
                return True
        
        self.fingerprint_list.append(fingerprint)
        return False


    def bytes_to_bits(self, bytes):
        return_bits = []
        for byte in bytes:
            for i in range(8):
                # Access bit at 0: (left to right)
                # Ex. 10101110
                # Shift right 7 -> 00000001
                # Access bit at 1: (left to right)
                # Ex. 10101110
                # Shift right 6 -> 00000010
                # Isolate last bit -> 0
                bit = (byte >> (7 - i))
                bit &= 1
                return_bits.append(bit)
        
        return return_bits
    
    def compare_fingerprints(self, f1, f2):
        length = min(len(f1), len(f2))  # len(f1) should == len(f2), but just in case
        matches = 0
        for i in range(length):
            if f1[i] == f2[i]:
                matches += 1
        return matches / length

if __name__ == "__main__":
    near_detector = NearDetector(0.6)

    words1 = ["a"]
    words2 = ["a"]
    print(near_detector.is_near_duplicate(words1))
    print(near_detector.is_near_duplicate(words2))

    words3 = ["the", "fatter", "catter", "satter", "on", "the", "antimatter"]
    words4 = ["this", "should", "not", "be", "flagged", "as", "similar"]
    words5 = ["this", "should", "catter", "satter", "on", "the", "antimatter"]
    print(near_detector.is_near_duplicate(words3))
    print(near_detector.is_near_duplicate(words4))
    print(near_detector.is_near_duplicate(words5))