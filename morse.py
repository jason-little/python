import string
uwords = set()
words = ["gin", "zen", "gig", "msg"]

k = list(string.ascii_lowercase)
v = [".-","-...","-.-.","-..",".","..-.","--.","....","..",".---","-.-",".-..","--","-.","---",".--.","--.-",".-.","...","-","..-","...-",".--","-..-","-.--","--.."]
dictionary = dict(zip(k, v))
word = ""
for i in words:
	for j in i:
		word = word + dictionary[j]
	uwords.add(word)
	word = ""

print(len(uwords))
