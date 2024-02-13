from MeowerBot import Bot, cbids
from MeowerBot.context import Context
from MeowerBot.cog import Cog
from MeowerBot.command import command
import requests
import logging
import time
from local_simple_database import LocalSimpleDatabase
from urllib import parse as urlencode

from os import environ as env

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("websockets.client").setLevel(level=logging.INFO)

headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8","Accept-Encoding":"gzip, deflate, br","Accept-Language":"en-GB,en;q-0.5","Connection":"keep-alive","Host":"www.dominos.co.uk","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"}
path = ""
bot = Bot()
LSD = LocalSimpleDatabase(path)
bridges = {}

def set_global_var(var_name, var_value):
    globals()[var_name] = var_value

def get_global_var(var_name):
    return globals()[var_name]

def append_global_list(global_list_name, string_to_append):
	globals().get(global_list_name).append(string_to_append)

def parse_args(args):
	message = ""
	for i in args:
		message = f'{message}{i} '
	message = message[:-1]
	print(message)
	return message


#dominos code
def nearest_store(postcode):
	global headers
	response = requests.get(f'https://www.dominos.co.uk/api/location/v1/search?searchText={postcode}',headers=headers)
	addresses =response.json()
	try:
		token = addresses["data"]["items"][0]["locationToken"]
	except:
		return None
	response = requests.get(f"https://www.dominos.co.uk/api/stores/v1/stores?locationToken={token}",headers=headers)
	try:
		print("succeeded 1")
		storeid = response.json()["data"]["localStore"]["id"]
		print("succeeded 2")
	except:
		return None
	return storeid

def store_menu(storeid):
	global headers
	response = requests.get(f'https://www.dominos.co.uk/api/menus/v1/menus/complete-menu/{storeid}',headers=headers)
	return response.json()
	
#bot code
@bot.event
async def login(t):
	print("Logged in!")

@bot.command(name="echo",args=20000000)
async def echo(ctx: Context,*args):
	if not ctx.user.username == "EngineerRunner" or ctx.user.username == "DominosBot":
		ctx.reply("you aint admin and for some reason this command is admin locked")
		return
	message = ""
	for i in args:
		message = f'{message}{i} '
	await ctx.send_msg(message)

@bot.command(name="spam",args=20000000)
async def spam(ctx: Context,*args):
	if not ctx.user.username == "EngineerRunner" or ctx.user.username == "DominosBot":
		await ctx.reply("you aint admin and for some reason this command is admin locked")
		return
	while True:
		await ctx.reply("sup")
		time.sleep(1)
@bot.command(name="echo-username",args=1)
async def echousername(ctx: Context):
	await ctx.send_msg(ctx.user.username)

@bot.command(name="test",args=1)
async def test(ctx: Context):
	await ctx.send_msg("this command works")
	print(ctx.message.chat.id)

@bot.command(name="register-postcode",args=2)
async def postcoderegister(ctx: Context,postcode1, postcode2):
	if ctx.message.chat.id == "home":
		await ctx.reply("to register a postcode, DM me the command instead. if you put a postcode here please delete/edit your message as its a stupid idea to put it in public chat")
		return
	username = str(ctx.user.username)
	if len(postcode1) != 4 or len(postcode1) != 3:
		await ctx.reply("that doesn't seem to be a uk postcode")
	elif len(postcode2) != 3:
		await ctx.reply("that doesn't seem to be a UK postcode.")
	LSD[f"str_{str(username)}_postcode"] = postcode1 + "%20" + postcode2
	await ctx.reply("your postcode has been registered. it will become unregistered at midnight UTC every day. for security reasons, i recommend you delete the message with the postcode in.")
	
@bot.command(name="nearest-store")
async def get_nearest_store(ctx: Context):
	if ctx.message.chat.id == "home":
		await ctx.reply("to get your local store, DM me the command instead. this is for security reasons so people can't get the general area you live.")
		return
	
	postcode = LSD["str_"+str(ctx.user.username)+"_postcode"]
	if len(postcode) < 5:
		await ctx.reply("you have not registered your postcode. to do so, run '@DominosBot register-postcode [your-postcode]'.")
		return
	neareststore = nearest_store(postcode)
	LSD[f"str_{str(ctx.user.username)}_store_id"] = neareststore
	await ctx.reply(f'the ID of your nearest store is {neareststore}. this has been saved for your next order, and will be deleted at midnight UTC.')

@bot.command(name="about")
async def about(ctx:Context):
	await ctx.send_msg("this bot will allow you to order from Dominos UK/ROI. to get started, DM this bot with the command '@DominosBot register-postcode [a UK postcode]'")

@bot.command(name="start-order")
async def new_order(ctx:Context):
	postcode = LSD["str_"+str(ctx.user.username)+"_postcode"]
	if len(postcode) < 5:
		await ctx.reply("you have not registered your UK/ROI postcode. to do so, run '@DominosBot register-postcode [your-postcode]' in DMs.")
		return
	storeID = LSD[f"str_{str(ctx.user.username)}_store_id"]
	if len(storeID) < 2:
		storeID = nearest_store(postcode)
		LSD[f"str_{str(ctx.user.username)}_store_id"] = storeID
	set_global_var(f'{ctx.user.username}_ongoing_order', True)
	set_global_var(f'{ctx.user.username}_basket', [])
	set_global_var(f'{ctx.user.username}_fake_order', False)
	await ctx.reply("order started!")
	
@bot.command(name="gpt",args=5000)
async def gptcommand(ctx:Context,*args):
	time.sleep(5)
	await ctx.reply("do i look like a f#cking ai")

@bot.command(name="get-menu",args=1)
async def menu(ctx:Context,menusection):
	try:
		if get_global_var(f'{ctx.user.username}_ongoing_order') != True:
			await ctx.send_msg("you need to start an order with '@DominosBot start-order'")
			return
	except:
		await ctx.send_msg("you need to start an order with '@DominosBot start-order'")
		return
	if menusection == "Pizza":
		await ctx.send_msg("Error: Pizza is a category with multiple subcategories. Try 'SpecialityPizza', 'Plant-BasedPizza', 'Gluten-FreePizza' or 'CustomPizza'.")
		return
	sections = ["SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps","Sides","Drinks"]
	if not menusection in sections:
		await ctx.send_msg('''Error: That isn't a category. Try "SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps","Sides" or "Drinks".''')
		return
	if get_global_var(f'{ctx.user.username}_fake_order'):
		menu = store_menu(28402)
	else:	
		menu = store_menu(LSD[f"str_{str(ctx.user.username)}_store_id"])
	if menusection == "Drinks":
		drinks = menu["data"]["fulfilments"][0]["menu"]["categories"][3]["subcategories"][0]["products"]
		message = "List of drinks: "
		for i in drinks:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "Sides":
		sides = menu["data"]["fulfilments"][0]["menu"]["categories"][1]["subcategories"][0]["products"]
		message = "List of sides: "
		for i in sides:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "Desserts":
		print(menu["data"])
		desserts = menu["data"]["fulfilments"][0]["menu"]["categories"][2]["subcategories"][0]["products"]
		message = "List of desserts: "
		for i in desserts:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "Wraps":
		print(menu["data"])
		wraps = menu["data"]["fulfilments"][0]["menu"]["categories"][4]["subcategories"][0]["products"]
		message = "List of wraps: "
		for i in wraps:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "CustomPizza":
		print(menu["data"])
		pizzas = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][0]["products"]
		message = "List of custom pizza: "
		for i in pizzas:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "SpecialityPizza":
		print(menu["data"])
		pizzas = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][1]["products"]
		message = "List of speciality pizza: "
		for i in pizzas:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "Plant-BasedPizza":
		print(menu["data"])
		pizzas = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][2]["products"]
		message = "List of plant-based pizza: "
		for i in pizzas:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return
	if menusection == "Gluten-FreePizza":
		print(menu["data"])
		pizzas = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][3]["products"]
		message = "List of gluten free pizza: "
		for i in pizzas:
			message = message + i["name"] + ", "
		await ctx.send_msg(message)
		return

@bot.command(name="add-to-basket",args=5)
async def basket_add(ctx:Context,menusection,*itemlist):
	print(itemlist)
	item = parse_args(itemlist)
	try:
		if get_global_var(f'{ctx.user.username}_ongoing_order') != True:
			await ctx.send_msg("you need to start an order with '@DominosBot start-order'")
	except:
		await ctx.send_msg("you need to start an order with '@DominosBot start-order'")
	if menusection == "Pizza":
		await ctx.send_msg("Error: Pizza is a category with multiple subcategories. Try 'Speciality Pizza', 'Plant-Based Pizza', 'Gluten Free Pizza' or 'Custom Pizza'.")
		return
	sections = ["SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps","Sides","Drinks"]
	if not menusection in sections:
		await ctx.send_msg('''Error: That isn't a category. Try "SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps", "Sides" or "Drinks".''')
		return
	if get_global_var(f'{ctx.user.username}_fake_order'):
		menu = store_menu(28402)
		print(menu)
	else:	
		menu = store_menu(LSD[f"str_{str(ctx.user.username)}_store_id"])
	if menusection == "Drinks":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][3]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "Sides":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][1]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "Desserts":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][2]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "Wraps":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][4]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "CustomPizza":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "SpecialityPizza":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][1]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "Plant-BasedPizza":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][2]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	if menusection == "Gluten-FreePizza":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][0]["subcategories"][3]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		if not item in itemnames:
			await ctx.send_msg("Error: Item does not exist. Make sure to copy the name exactly.")
			return
		append_global_list(f'{ctx.user.username}_basket',item)
		await ctx.send_msg(f'Successfully added {item} to basket!')
		return
	
@bot.command(name="view-basket",args=0)
async def basket_view(ctx:Context):
	try:
		basketlist = get_global_var(f'{ctx.user.username}_basket')
	except:
		await ctx.send_msg("you don't have an order started.")
	message = ""
	for i in basketlist:
		message = f'{message}{i}, '
	message = f'Your basket: {message}'
	message = message[:-1]
	await ctx.send_msg(message)

@bot.command(name="finish-order",args=0)
async def finish_order(ctx:Context):
	try:
		basketlist = get_global_var(f'{ctx.user.username}_basket')
	except:
		await ctx.send_msg("you don't have an order started.")
	message = ""
	for i in basketlist:
		message = f'{message}{i}, '
	message = message[:-1]
	message = message[:-1]
	set_global_var(f'{ctx.user.username}_ongoing_order', False)
	set_global_var(f'{ctx.user.username}_basket', [])
	set_global_var(f'{ctx.user.username}_fake_order', False)
	await ctx.send_msg(f"currently you can't actually order ): but thanks for getting the following: {message}")
	

@bot.command(name="start-generic-order",args=0)
async def generic_order(ctx:Context):
	await ctx.send_msg("you have started an order with the generic store id of: 28402")
	set_global_var(f'{ctx.user.username}_ongoing_order', True)
	set_global_var(f'{ctx.user.username}_fake_order', True)
	set_global_var(f'{ctx.user.username}_basket', [])

@bot.command(name="start-poll",args=1)
async def pizza_poll(ctx:Context, category):
	ctx.reply("this command does not exist yet")
	if 1 == 1:
		return
	try:
		if get_global_var(f'{ctx.user.username}_ongoing_order') != True:
			await ctx.send_msg("you need to start an order with '@DominosBot start-order'")
	except:
		await ctx.send_msg("you need to start an order with '@DominosBot start-order' or '@DominosBot start-generic-order'")
	if category == "Pizza":
		await ctx.send_msg("Error: Pizza is a category with multiple subcategories. Try 'Speciality Pizza', 'Plant-Based Pizza', 'Gluten Free Pizza' or 'Custom Pizza'.")
		return
	sections = ["SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps","Sides","Drinks"]
	if not category in sections:
		await ctx.send_msg('''Error: That isn't a category. Try "SpecialityPizza", "Plant-BasedPizza", "Gluten-FreePizza", "CustomPizza", "Wraps", "Sides" or "Drinks".''')
		return
	if category == "CustomPizza":
		await ctx.send_msg("Error: the custom pizza is 1 option for create your own, and i havent programmed this yet so :shrug:")
		return
	if category == "Wraps":
		items = menu["data"]["fulfilments"][0]["menu"]["categories"][4]["subcategories"][0]["products"]
		itemnames = []
		for i in items:
			itemnames.append(i["name"])
		message = ""
		for i in itemnames:
			message = f'{message}{i}, '
		poll = {}
		#for i in itemnames
			#poll.update({"i":0})
		
		message = f'vote on the next menu item to be added to the basket! options: {message}'
		set_global_var(f'{ctx.user.username}_poll_votes',poll)
		set_global_var(f'{ctx.user.username}_ongoing_poll',itemnames)
		done = False
		time = 60
		while not done == True:
			a = a
		#append_global_list(f'{ctx.user.username}_basket',item)
		#await ctx.send_msg(f'Successfully added {item} to basket!')
		return

@bot.command(name="help",args=0)
async def generic_order(ctx:Context):
	await ctx.send_msg('''hi im dominosbot, here are my commands \n DM commands: \n "@DominosBot register-postcode [postcode]" registers a UK/ROI postcode, not tested thoroughly but should work \n "@DominosBot nearest-store" gets the ID of nearest store. requires registered postcode \n order starting commands: \n "@DominosBot start-order" starts order at nearest store. requires postcode. \n "@DominosBot start-generic-order" starts order with the api default store for people outside of UK/ROI (or people smart enough to not give me their location) \n order commands (all require ongoing order): \n "@DominosBot get-menu [menu section]" gets the menu for a section of the menu. must be correctly capitalised \n "@DominosBot add-to-basket [menu section] [EXACT item name]" adds item to basket from menu section \n "@DominosBot view-basket" views basket \n "@DominosBot finish-order" doesn't actually order yet but ends order and clears basket \n crap commands: \n "@DominosBot gpt [command]" does gpt crap''')
# Allows users to do math equations such as "535 * 3"


@bot.command(name="math",args=10000)
async def do_math_equation(ctx:Context,*args):
	if ctx.user.username == "EngineerRunner":
		ctx.message._id
		cmdz = ""
		for i in args:
			cmdz = cmdz + i + " "
		print(cmdz)
		output = eval(cmdz)
		print(output)
		await ctx.reply(output)
	else:
		await ctx.reply("no")

bot.run("DominosBot", "this aint my password")
