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
ITEM_STOCK_WINDOW_SIZE = (400, 500)
ITEM_STOCK_GRID_COLUMN_NAMES = ('Name:', 'Balance:', 'Belt level:')
ITEM_STOCK_GRID_COLUMN_WIDTHS = (25, 17, 10)
ITEM_STOCK_DISPLAY_PRECISION = 3
# Global variables:
recipeBook = None
itemStock = None
allItems = set()

def itemCount2BeltLevel(itemCount):
	if itemCount <= 60:
		return 1
	elif itemCount <= 120:
		return 2
	elif itemCount <= 270:
		return 3
	elif itemCount <= 480:
		return 4
	elif itemCount <= 960:
		return 5
	else:
		return 0  # One belt not enough

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
	def __init__(self, root):
		self.consumption = {}
		self.production = {}
		self.balanceStrVars = {}
		for item in sorted(allItems):
			self.balanceStrVars[item] = tk.StringVar(root, '0')
		self.calcStock()

	def getBalanceStrVar(self, item):
		return self.balanceStrVars[item]

	def getProduction(self, item):
		return self.production.get(item, 0)

	def getItems(self):
		return self.balanceStrVars.keys()

	def calcStock(self):
		self.consumption.clear()
		self.production.clear()
		for i in range(recipeBook.getSize()):
			for item in recipeBook.getEducts(i):
				self.consumption[item] = self.consumption.get(item, 0) + recipeBook.getEducts(i)[item] * recipeBook.getUsageCount(i)
			for item in recipeBook.getProducts(i):
				self.production[item] = self.production.get(item, 0) + recipeBook.getProducts(i)[item] * recipeBook.getUsageCount(i)
		for item, balanceStrVar in self.balanceStrVars.items():
			balanceStrVar.set(str(round(self.production.get(item, 0) - self.consumption.get(item, 0), ITEM_STOCK_DISPLAY_PRECISION)))

class GridField():
	class Type(Enum):
		Header = auto()
		Label = auto()
		DynamicLabel = auto()
		DigitEntry = auto()

	def isFloatOrEmpty(text):
		if str(text) == '' or (text.lstrip('-').replace('.', '').isdigit() and text.count('.') <= 1):
			return True
		else:
			return False

	def add(root, row, column, width, type, arg=None, callback=None):
		if type == GridField.Type.DigitEntry:
			arg.trace_add('write', callback)
			vcmd = (root.register(GridField.isFloatOrEmpty), '%P')
			gridField = tk.Entry(root, justify='center', width=width, textvariable=arg, validate='key', validatecommand=vcmd)
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
	root.geometry(str(RECIPE_BOOK_WINDOW_SIZE[0]) + 'x' + str(RECIPE_BOOK_WINDOW_SIZE[1]))
	root.resizable(0, 1)
	# Set up scrollable main frame:
	outerFrame = tk.Frame(root)
	outerFrame.pack(fill=tk.BOTH, expand=1)
	outerCanvas = tk.Canvas(outerFrame)
	outerCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
	outerScrollbar = tk.Scrollbar(outerFrame, orient=tk.VERTICAL, command=outerCanvas.yview)
	outerScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	outerCanvas.configure(yscrollcommand=outerScrollbar.set)
	outerCanvas.bind('<Configure>', lambda event: outerCanvas.configure(scrollregion=outerCanvas.bbox('all')))
	mainFrame = tk.Frame(outerCanvas)
	outerCanvas.create_window((0, 0), window=mainFrame, anchor='nw')
	# Create recipe book grid field:
	recipeBook = RecipeBook(mainFrame)
	row = 0
	column = 0
	GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, RECIPE_BOOK_GRID_COLUMN_NAMES[column])
	column += 1
	GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, RECIPE_BOOK_GRID_COLUMN_NAMES[column])
	column += 1
	GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, RECIPE_BOOK_GRID_COLUMN_NAMES[column])
	for i in range(recipeBook.getSize()):
		row = i + 1
		column = 0
		GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.DigitEntry, recipeBook.getUsageCountStrVar(i), recipeBook.usageCountCallback)
		column += 1
		GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, itemDict2Str(recipeBook.getProducts(i)))
		column += 1
		GridField.add(mainFrame, row, column, RECIPE_BOOK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, itemDict2Str(recipeBook.getEducts(i)))

def createItemsBalanceWindow(root):
	global itemStock
	root.title('Items Balance')
	root.geometry(str(ITEM_STOCK_WINDOW_SIZE[0]) + 'x' + str(ITEM_STOCK_WINDOW_SIZE[1]))
	root.resizable(0, 1)
	# Set up scrollable main frame:
	outerFrame = tk.Frame(root)
	outerFrame.pack(fill=tk.BOTH, expand=1)
	outerCanvas = tk.Canvas(outerFrame)
	outerCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
	outerScrollbar = tk.Scrollbar(outerFrame, orient=tk.VERTICAL, command=outerCanvas.yview)
	outerScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	outerCanvas.configure(yscrollcommand=outerScrollbar.set)
	outerCanvas.bind('<Configure>', lambda event: outerCanvas.configure(scrollregion=outerCanvas.bbox('all')))
	mainFrame = tk.Frame(outerCanvas)
	outerCanvas.create_window((0, 0), window=mainFrame, anchor='nw')
	# Create item stock grid field:
	itemStock = ItemStock(mainFrame)
	row = 0
	column = 0
	GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, ITEM_STOCK_GRID_COLUMN_NAMES[column])
	column += 1
	GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, ITEM_STOCK_GRID_COLUMN_NAMES[column])
	column += 1
	GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Header, ITEM_STOCK_GRID_COLUMN_NAMES[column])
	row = 0
	for item in itemStock.getItems():
		row += 1
		column = 0
		GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, item)
		column += 1
		GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.DynamicLabel, itemStock.getBalanceStrVar(item))
		column += 1
		GridField.add(mainFrame, row, column, ITEM_STOCK_GRID_COLUMN_WIDTHS[column], GridField.Type.Label, str(itemCount2BeltLevel(itemStock.getProduction(item))))

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