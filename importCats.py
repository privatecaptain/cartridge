import json
from cartridge.shop.models import Category

f = open('orcat.json','r')

jcats = json.loads(f.readlines()[0])

print(len(jcats))

n = 0 
for cat in jcats:
	c = Category.objects.get_or_create(title=cat['title'])
	for k in cat:
		c.__dict__[k] =cat[k]
	c.save()
	n += 1

print(n)
