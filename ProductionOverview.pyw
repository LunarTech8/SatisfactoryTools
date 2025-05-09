import traceback
from enum import Enum, auto
import tkinter as tk

# TODO: use better UI (https://medium.com/@fareedkhandev/modern-gui-using-tkinter-12da0b983e22)

# Configurables:
RECIPES_FORMAT_FIELD_SEPARATOR = ' '
RECIPES_FORMAT_ITEMS_SEPARATOR = '+'
RECIPES_FORMAT_ITEM_SEPARATOR = ':'
RECIPES_FORMAT_EMPTY_ITEM = '-'
RECIPE_BOOK_WINDOW_SIZE = (910, 500)
RECIPE_BOOK_GRID_COLUMN_NAMES = ('Usage count:', 'Products:', 'Educts:')
RECIPE_BOOK_GRID_COLUMN_WIDTHS = (10, 40, 75)
ITEM_STOCK_WINDOW_SIZE = (412, 500)
ITEM_STOCK_GRID_COLUMN_NAMES = ('Name:', 'Balance:', 'Belt/Pipe level:')
ITEM_STOCK_GRID_COLUMN_WIDTHS = (25, 17, 12)
ITEM_STOCK_DISPLAY_PRECISION = 3
# Global variables:
recipeBook = None
itemStock = None
allItems = set()

def itemCount2BeltLevelStr(itemCount, usePipe):
	if usePipe:
		suffix = ' [P]'
		if itemCount <= 0:
			return '0' + suffix
		elif itemCount <= 300:
			return '1' + suffix
		elif itemCount <= 600:
			return '2' + suffix
		elif itemCount <= 600+300:
			return '2+1' + suffix
		elif itemCount <= 600+600:
			return '2+2' + suffix
		elif itemCount <= 600+600+300:
			return '2+2+1' + suffix
		elif itemCount <= 600+600+600:
			return '2+2+2' + suffix
	else:
		suffix = ' [B]'
		if itemCount <= 0:
			return '0' + suffix
		elif itemCount <= 60:
			return '1' + suffix
		elif itemCount <= 120:
			return '2' + suffix
		elif itemCount <= 270:
			return '3' + suffix
		elif itemCount <= 480:
			return '4' + suffix
		elif itemCount <= 960:
			return '5' + suffix
		elif itemCount <= 960+60:
			return '5+1' + suffix
		elif itemCount <= 960+120:
			return '5+2' + suffix
		elif itemCount <= 960+270:
			return '5+3' + suffix
		elif itemCount <= 960+480:
			return '5+4' + suffix
		elif itemCount <= 960+960:
			return '5+5' + suffix
	return 'INVALID'

def isUsingPipe(item):
	if item in ('Water', 'NitrogenGas', 'SulfuricAcid', 'CrudeOil', 'HeavyOilResidue', 'AluminaSolution', 'Fuel'):
		return True
	else:
		return False

def itemDict2Str(itemDict):
	itemFields = []
	for item in itemDict:
		itemFields.append(item + ' (' + str(itemDict[item]) + ')')
	if len(itemFields) <= 0:
		itemFields.append(RECIPES_FORMAT_EMPTY_ITEM)
	return ', '.join(itemFields)

class Recipe:
	def __init__(self, root, usageCount, educts, products):
		self.usageCountStrVar = tk.StringVar(root, str(usageCount))
		self.educts = educts
		self.products = products

class RecipeBook:
	FILE_NAME = 'ProductionRecipes.txt'

	def __init__(self, root):
		self.recipes = []
		self.readRecipes(root)

	def getSize(self):
		return len(self.recipes)

	def getUsageCountStrVar(self, recipeIdx):
		return self.recipes[recipeIdx].usageCountStrVar

	def getUsageCount(self, recipeIdx):
		if self.recipes[recipeIdx].usageCountStrVar.get() == '':
			return 0
		else:
			return float(self.recipes[recipeIdx].usageCountStrVar.get())

	def getEducts(self, recipeIdx):
		return self.recipes[recipeIdx].educts

	def getProducts(self, recipeIdx):
		return self.recipes[recipeIdx].products

	def readRecipes(self, root):
		recipesFile = open(RecipeBook.FILE_NAME, 'r')
		lines = recipesFile.readlines()
		self.recipes.clear()
		for line in lines:
			fieldsFormated = line.strip().split(RECIPES_FORMAT_FIELD_SEPARATOR)
			# Get usage count:
			fieldIdx = 0
			usageCount = float(fieldsFormated[fieldIdx])
			# Get products:
			fieldIdx += 1
			products = {}
			productsFormated = fieldsFormated[fieldIdx].split(RECIPES_FORMAT_ITEMS_SEPARATOR)
			for productFormated in productsFormated:
				count, name = productFormated.split(RECIPES_FORMAT_ITEM_SEPARATOR)
				products[name] = float(count)
				allItems.add(name)
			# Get educts:
			fieldIdx += 1
			educts = {}
			eductsFormated = fieldsFormated[fieldIdx].split(RECIPES_FORMAT_ITEMS_SEPARATOR)
			if eductsFormated != [RECIPES_FORMAT_EMPTY_ITEM]:
				for eductFormated in eductsFormated:
					count, name = eductFormated.split(RECIPES_FORMAT_ITEM_SEPARATOR)
					educts[name] = float(count)
					allItems.add(name)
			# Create recipes:
			self.recipes.append(Recipe(root, usageCount, educts, products))
		self.recipes.sort(key=lambda recipe: next(iter(recipe.products.keys())))

	def writeRecipes(self):
		recipesFormated = []
		for i in range(self.getSize()):
			fieldsFormated = []
			# Add usage count:
			fieldsFormated.append(str(self.getUsageCount(i)))
			# Add products:
			productsFormated = []
			for product in self.getProducts(i):
				productsFormated.append(str(self.getProducts(i)[product]) + RECIPES_FORMAT_ITEM_SEPARATOR + product)
			fieldsFormated.append(RECIPES_FORMAT_ITEMS_SEPARATOR.join(productsFormated))
			# Add educts:
			eductsFormated = []
			for educt in self.getEducts(i):
				eductsFormated.append(str(self.getEducts(i)[educt]) + RECIPES_FORMAT_ITEM_SEPARATOR + educt)
			if len(eductsFormated) <= 0:
				eductsFormated.append(RECIPES_FORMAT_EMPTY_ITEM)
			fieldsFormated.append(RECIPES_FORMAT_ITEMS_SEPARATOR.join(eductsFormated))
			# Join fields:
			recipesFormated.append(RECIPES_FORMAT_FIELD_SEPARATOR.join(fieldsFormated))
		with open(RecipeBook.FILE_NAME, 'w') as recipesFile:
			recipesFile.write('\n'.join(recipesFormated))

	def usageCountCallback(self, name, index, mode):
		for i in range(self.getSize()):
			usageCountStrVar = self.getUsageCountStrVar(i)
			if str(usageCountStrVar) == name:
				if usageCountStrVar.get() != '':
					itemStock.calcStock()
					self.writeRecipes()
				break

class ItemStock:
	EPSILON = pow(10, -ITEM_STOCK_DISPLAY_PRECISION)

	def __init__(self, root):
		self.consumption = {}
		self.production = {}
		self.balanceStrVars = {}
		self.beltLevelStrVars = {}
		for item in sorted(allItems):
			self.balanceStrVars[item] = tk.StringVar(root, '0')
			self.beltLevelStrVars[item] = tk.StringVar(root, '0')
		self.calcStock()

	def getBalanceStrVar(self, item):
		return self.balanceStrVars[item]

	def getBeltLevelStrVar(self, item):
		return self.beltLevelStrVars[item]

	def getProduction(self, item):
		return self.production.get(item, 0)

	def getItems(self):
		return self.balanceStrVars.keys()

	def prettyFloatStr(self, value):
		roundedValue = round(value, ITEM_STOCK_DISPLAY_PRECISION)
		roundedValueStr = str(roundedValue)
		if roundedValue < ItemStock.EPSILON and roundedValue > -ItemStock.EPSILON:
			return '0.0'
		elif len(roundedValueStr) >= 5 and roundedValueStr[-1] == '9' and roundedValueStr[-4] == '.':
			return str(roundedValue + ItemStock.EPSILON)
		else:
			return roundedValueStr

	def calcStock(self):
		self.consumption.clear()
		self.production.clear()
		for i in range(recipeBook.getSize()):
			for item in recipeBook.getEducts(i):
				self.consumption[item] = self.consumption.get(item, 0) + recipeBook.getEducts(i)[item] * recipeBook.getUsageCount(i)
			for item in recipeBook.getProducts(i):
				self.production[item] = self.production.get(item, 0) + recipeBook.getProducts(i)[item] * recipeBook.getUsageCount(i)
		for item, balanceStrVar in self.balanceStrVars.items():
			balanceStrVar.set(self.prettyFloatStr(self.production.get(item, 0) - self.consumption.get(item, 0)))
		for item, beltLevelStrVar in self.beltLevelStrVars.items():
			beltLevelStrVar.set(itemCount2BeltLevelStr(self.production.get(item, 0), isUsingPipe(item)))

class GridField():
	GRID_FIELD_ENTRY_WIDTH_ADDITION = 2

	class Type(Enum):
		Header = auto()
		Label = auto()
		DynamicLabel = auto()
		DigitEntry = auto()

	def isFloatOrEmpty(text):
		return str(text) == '' or (text.lstrip('-').replace('.', '').isdigit() and text.count('.') <= 1)

	def add(root, row, column, width, type, arg=None, callback=None):
		if type == GridField.Type.DigitEntry:
			if callback is not None:
				arg.trace_add('write', callback)
			vcmd = (root.register(GridField.isFloatOrEmpty), '%P')
			gridField = tk.Entry(root, justify='center', width=width+GridField.GRID_FIELD_ENTRY_WIDTH_ADDITION, textvariable=arg, validate='key', validatecommand=vcmd)
		elif type == GridField.Type.Label:
			gridField = tk.Label(root, text=arg, borderwidth=2, relief='sunken', width=width)
		elif type == GridField.Type.DynamicLabel:
			gridField = tk.Label(root, textvariable=arg, borderwidth=2, relief='sunken', width=width)
		elif type == GridField.Type.Header:
			gridField = tk.Label(root, text=arg, borderwidth=2, relief='groove', width=width)
		else:
			raise AttributeError('Invalid grid field type')
		gridField.grid(row=row, column=column)

def createProductionRecipesWindow(root):
	global recipeBook
	root.title('Production Recipes')
	root.geometry(f"{RECIPE_BOOK_WINDOW_SIZE[0]}x{RECIPE_BOOK_WINDOW_SIZE[1]}")
	root.resizable(0, 1)
	# Set up main frame with fixed header frame and scrollable content frame:
	contentFrame = tk.Frame(root)
	contentFrame.pack(fill=tk.BOTH, expand=1)
	headerFrame = tk.Frame(contentFrame)
	headerFrame.pack(fill=tk.X)
	mainFrame = tk.Frame(contentFrame)
	mainFrame.pack(fill=tk.BOTH, expand=1)
	outerCanvas = tk.Canvas(mainFrame)
	outerCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
	outerScrollbar = tk.Scrollbar(mainFrame, orient=tk.VERTICAL, command=outerCanvas.yview)
	outerScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	outerCanvas.configure(yscrollcommand=outerScrollbar.set)
	outerCanvas.bind('<Configure>', lambda event: outerCanvas.configure(scrollregion=outerCanvas.bbox('all')))
	contentFrame = tk.Frame(outerCanvas)
	outerCanvas.create_window((0, 0), window=contentFrame, anchor='nw')
	# Create recipe book grid field:
	recipeBook = RecipeBook(contentFrame)
	row = 0
	for column, name in enumerate(RECIPE_BOOK_GRID_COLUMN_NAMES):
		GridField.add(headerFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, name)
	for i in range(recipeBook.getSize()):
		row = i + 1
		column = 0
		GridField.add(contentFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.DigitEntry, recipeBook.getUsageCountStrVar(i), recipeBook.usageCountCallback)
		column += 1
		GridField.add(contentFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, itemDict2Str(recipeBook.getProducts(i)))
		column += 1
		GridField.add(contentFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, itemDict2Str(recipeBook.getEducts(i)))

def createItemsBalanceWindow(root):
	global itemStock
	root.title('Items Balance')
	root.geometry(f"{ITEM_STOCK_WINDOW_SIZE[0]}x{ITEM_STOCK_WINDOW_SIZE[1]}")
	root.resizable(0, 1)
	# Set up main frame with fixed header frame and scrollable content frame:
	contentFrame = tk.Frame(root)
	contentFrame.pack(fill=tk.BOTH, expand=1)
	headerFrame = tk.Frame(contentFrame)
	headerFrame.pack(fill=tk.X)
	mainFrame = tk.Frame(contentFrame)
	mainFrame.pack(fill=tk.BOTH, expand=1)
	outerCanvas = tk.Canvas(mainFrame)
	outerCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
	outerScrollbar = tk.Scrollbar(mainFrame, orient=tk.VERTICAL, command=outerCanvas.yview)
	outerScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	outerCanvas.configure(yscrollcommand=outerScrollbar.set)
	outerCanvas.bind('<Configure>', lambda event: outerCanvas.configure(scrollregion=outerCanvas.bbox('all')))
	contentFrame = tk.Frame(outerCanvas)
	outerCanvas.create_window((0, 0), window=contentFrame, anchor='nw')
	# Create item stock grid field:
	itemStock = ItemStock(contentFrame)
	row = 0
	for column, name in enumerate(ITEM_STOCK_GRID_COLUMN_NAMES):
		GridField.add(headerFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, name)
	row = 0
	for item in itemStock.getItems():
		row += 1
		column = 0
		GridField.add(contentFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, item)
		column += 1
		GridField.add(contentFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.DynamicLabel, itemStock.getBalanceStrVar(item))
		column += 1
		GridField.add(contentFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.DynamicLabel, itemStock.getBeltLevelStrVar(item))

# TODO: use to improve init placement of windows
# def centerWindow(root):
#     windowWidth = root.winfo_width()
#     windowHeight = root.winfo_height()
#     windowX = int((root.winfo_screenwidth() / 2) - (windowWidth / 2))
#     windowY = int((root.winfo_screenheight() / 2) - (windowHeight / 2))
#     root.geometry(str(windowWidth) + 'x' + str(windowHeight) + '+' + str(windowX) + '+' + str(windowY))

def main():
	try:
		createProductionRecipesWindow(tk.Tk())
		createItemsBalanceWindow(tk.Tk())
		tk.mainloop()
	except Exception:
		print(traceback.format_exc())
		input('Press enter to close traceback.')

if __name__ == "__main__":
	main()