from cartridge.shop.models import (
    Category,
    Product,
    ProductImage,
    ProductOption,
    ProductVariation,
)
import csv
from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
import shutil

# images get copied from this directory
LOCAL_IMAGE_DIR = "/tmp/orig"
# images get copied to this directory under STATIC_ROOT
IMAGE_SUFFIXES = [
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".tif",
    ".gif",
    ".GIF",
    ".png",
    ".PNG",
]
EMPTY_IMAGE_ENTRIES = ["Please add", "N/A", ""]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

# Here we define what column headings are used in the csv.
TITLE = ("Title")
CONTENT = ("Content")
DESCRIPTION = ("Description")
SKU = ("SKU")
IMAGE = ("Image")
CATEGORY = ("Category")
SUB_CATEGORY = ("Sub-Category")
# SIZE = ("Size")
NUM_IN_STOCK = ("Number in Stock")
UNIT_PRICE = ("Unit Price")
SALE_PRICE = ("Sale Price")
SALE_START_DATE = ("Sale Start Date")
SALE_START_TIME = ("Sale Start Time")
SALE_END_DATE = ("Sale End Date")
SALE_END_TIME = ("Sale End Time")

DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
SITE_MEDIA_IMAGE_DIR = ("product")
PRODUCT_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, SITE_MEDIA_IMAGE_DIR)


TYPE_CHOICES = dict()
for id, choice in settings.SHOP_OPTION_TYPE_CHOICES:
    TYPE_CHOICES[choice] = id

fieldnames = [
    TITLE,
    CONTENT,
    DESCRIPTION,
    CATEGORY,
    SUB_CATEGORY,
    SKU,
    IMAGE,
    NUM_IN_STOCK,
    UNIT_PRICE,
    SALE_PRICE,
    SALE_START_DATE,
    SALE_START_TIME,
    SALE_END_DATE,
    SALE_END_TIME,
]









reader = csv.DictReader(open('p.csv','r'),delimiter=",")
ctgs = Category.objects.all()

def tagName(title):
	j = title.replace(' ','')
	j = j.lower()
	return j

catTag = {}

for cat in ctgs:
	catTag[tagName(cat.title)] = cat


cct = catTag.keys()

for row in reader:
	p = row
	ptags = row['Tags']
	lptags = ptags.split(',')
	mts = 0 #empty tags
	for i in lptags:
		if i == '':
			mts += 1
			print("Empty Tags: {} for ROW: {}. Category: {}".format(mts,p['Title'],p['Category']))
	for ptag in lptags:
		ptag = tagName(ptag)
		if ptag != '':
			cat = catTag[ptag]
			# print(cat)

for cat in catTag:
	ct = catTag[cat]
	print(ct.slug)

def _product_from_row(row):
    product, created = Product.objects.get_or_create(title=row[TITLE])
    product.content = row[CONTENT]
    product.description = row[DESCRIPTION]
    # TODO: set the 2 below from spreadsheet.
    product.status = CONTENT_STATUS_PUBLISHED
    product.available = True
    # TODO: allow arbitrary level/number of categories.
    base_cat, created = Category.objects.get_or_create(title=row[CATEGORY])
    sub_cat, created = Category.objects.get_or_create(
        title=row[SUB_CATEGORY], parent=base_cat
    )
    product.categories.add(sub_cat)
    # shop_cat, created = Category.objects.get_or_create(title="Shop")
    # product.categories.add(shop_cat)
    #Tag Categories

    tags = row['Tags']
    lptags = tags.split(',')
    for ptag in lptags:
        ptag = tagName(ptag)
        if ptag != '':
            cat = catTag[ptag]
            print(cat)
            product.categories.add(cat)
    product.save()
    return product

def _make_image(image_str, product):
    if image_str in EMPTY_IMAGE_ENTRIES:
        return None
    # try adding various image suffixes, if none given in original filename.
    root, suffix = os.path.splitext(image_str)
    if suffix not in IMAGE_SUFFIXES:
        raise CommandError("INCORRECT SUFFIX: %s" % image_str)
    image_path = os.path.join(LOCAL_IMAGE_DIR, image_str)
    if not os.path.exists(image_path):
        return None
    shutil.copy(image_path, PRODUCT_IMAGE_DIR)
    # shutil.copy(image_path, os.path.join(PRODUCT_IMAGE_DIR, "orig"))
    image, created = ProductImage.objects.get_or_create(
        file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, image_str)),
        description=image_str,  # TODO: handle column for this.
        product=product,
    )
    return image

def import_products(csv_file):
    print(("Importing .."))
    # More appropriate for testing.
    # Product.objects.all().delete()
    reader = csv.DictReader(open(csv_file), delimiter=",")
    for row in reader:
        print(row)
        product = _product_from_row(row)
        try:
            variation = ProductVariation.objects.create(
                # strip whitespace
                sku=row[SKU].replace(" ", ""),
                product=product,
            )
        except IntegrityError:
            raise CommandError("Product with SKU exists! sku: %s" % row[SKU])
        if row[NUM_IN_STOCK]:
            variation.num_in_stock = row[NUM_IN_STOCK]
        if row[UNIT_PRICE]:
            variation.unit_price = row[UNIT_PRICE]
        if row[SALE_PRICE]:
            variation.sale_price = row[SALE_PRICE]
        if row[SALE_START_DATE] and row[SALE_START_TIME]:
            variation.sale_from = _make_date(row[SALE_START_DATE], row[SALE_START_TIME])
        if row[SALE_END_DATE] and row[SALE_END_TIME]:
            variation.sale_to = _make_date(row[SALE_END_DATE], row[SALE_END_TIME])
        for option in TYPE_CHOICES:
            if row[option]:
                name = "option%s" % TYPE_CHOICES[option]
                setattr(variation, name, row[option])
                new_option, created = ProductOption.objects.get_or_create(
                    type=TYPE_CHOICES[option], name=row[option]  # TODO: set dynamically
                )
        variation.save()
        image = _make_image(row[IMAGE], product)
        if image:
            variation.image = image
        product.variations.manage_empty()
        product.variations.set_default_images([])
        product.copy_default_variation()
        product.save()

    print("Variations: %s" % ProductVariation.objects.all().count())
    print("Products: %s" % Product.objects.all().count())



import_products('p.csv')