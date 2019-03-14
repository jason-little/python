emails = ["test.email+alex@leetcode.com","test.e.mail+bob.cathy@leetcode.com","testemail+david@lee.tcode.com"]
email = set()
for i in emails:
	user = i.split("@")[0]
	domain = i.split("@")[1]
	user = user.split("+")[0]
	user = user.replace(".", "")
	email.add(user + "@" + domain)

print(len(email))