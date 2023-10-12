from aiogram import Bot, Dispatcher,executor, types
import motor.motor_asyncio
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime,timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup,KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bson.objectid import ObjectId
import asyncio
import re

#MongoDB (you need to create or rename this cluster + collections )
#probably rename ObjectId in 603 str.
cluster = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://_LOGIN:_PASSWORD@_CLUSTER.aigmpxp.mongodb.net/ttbot_db?retryWrites=true&w=majority")
collection = cluster.ttbot_db.ttbot_collection
video_collection = cluster.ttbot_db.videos
metadata_collection = cluster.ttbot_db.metadata

TOKEN="_BOT_TOKEN"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot,storage=MemoryStorage()) 


# Определение состояний
class Form(StatesGroup):
    card_number = State()  # Состояние сбора номера карты
    email = State()  # Состояние сбора адреса почты
    amount = State()  # Состояние сбора суммы денег


channel_log = Channel_id
#example:
#channel_log = -1001971599660

ad_msg_withdraw = '''Para enviar una solicitud de eliminación, debe estar suscrito al canal de nuestro patrocinador.

Este chico es un joven millonario de Perú, a la edad de 26 años ha logrado un éxito increíble en su trabajo y ahora ayuda a las personas a ganar dinero en línea y comparte esta información en su canal.


Suscríbete a tu canal ahora mismo, mira de 5 a 10 publicaciones y haz clic para confirmar la suscripción✅'''
#Постоянная клавиатура
main = ReplyKeyboardMarkup()

btn_1 = KeyboardButton('Ver vídeos y ganar dinero 📺')
btn_2 = KeyboardButton('Reglas 🎯')
btn_3 = KeyboardButton('📱 Mi perfil')
btn_4 = KeyboardButton('Retirada de dinero  🏧')
btn_5 = KeyboardButton('💰 Ganar aún más dinero 💰')
btn_6 = KeyboardButton('Canal')
main.add(btn_1).add(btn_2).row(btn_3,btn_4).add(btn_5)
main_canal = ReplyKeyboardMarkup().add(btn_1).row(btn_2,btn_6).row(btn_3,btn_4).add(btn_5)
#Клавиатура Админа
admin_main = ReplyKeyboardMarkup()

adbtn_2 = KeyboardButton('/all_videos')
# adbtn_3 = KeyboardButton('/set_videos')
adbtn_4 = KeyboardButton('/member')
adbtn_5 = KeyboardButton('/set_admin')
adbtn_6 = KeyboardButton('/stats')
adbtn_7 = KeyboardButton('/ad')
adbtn_8 = KeyboardButton('/start')

admin_main.row(adbtn_7,adbtn_4).row(adbtn_5,adbtn_6).row(adbtn_2,adbtn_8)


async def add_user(user_id,referr,username):
    date = datetime.now()
    time_now = int(date.timestamp())
    collection.insert_one({
        "_id": user_id,
        "date": str(date),
        "watching": time_now,
        "balance": 0,
        "referr": referr,
        "referrals": 0 ,
        "rereferrals": 0,
        "username": username,
        "today_left": 20,
        "update_limit": time_now,
        "isadmin": 0,
        "watched_videos":0,
        "queue" : 1,
        "ismember":0,
        "multiply" :1,
        "requested":0,
        "requested_time":0
    })

async def is_valid_email(email):
    # Определение шаблона для валидации email-адреса
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)

# +1 Реферрал
async def ref(referr):
    #+1
    r = await collection.update_one({"_id" : referr},{"$inc":{"referrals": 1,"balance":5}})
    #NOTICE REFERR
    if r.matched_count > 0:
        r = await collection.find_one({"_id":referr})
        balance = r.get("balance")
        referrals = r.get("referrals")
        rereferrals = r.get("rereferrals")
        try:
            await bot.send_message(referr,f'''🎉 Alguien se registró en el bot usando su enlace 🎉

<b>+ 5 Sol</b> 💰 

📢 Has invitado a: <b>{referrals} usuarios</b>
📣 Tus amigos han invitado a: <b>{rereferrals} usuarios</b>
💸 Su saldo: <b>{balance} Sol</b>''',parse_mode="HTML",disable_notification = True)
        except:
            print("Msg send error")
        else:
            print('user not find')

# +1 Ререферрал
async def reref(rereferr):
    r = await collection.update_one({"_id" : rereferr},{"$inc":{"rereferrals": 1,"balance": 4}})

    #NOTICE REREFERR
    if r.matched_count > 0:
        r = await collection.find_one({"_id":rereferr})
        balance = r.get("balance")
        referrals = r.get("referrals")
        rereferrals = r.get("rereferrals")
        try:
            await bot.send_message(rereferr,f'''🎉 Alguien se registró en el bot utilizando el enlace de tu amigo. 🎉

<b>+ 2.5 Sol</b> 💰 

📢 Has invitado a: <b>{referrals} usuarios</b>
📣 Tus amigos han invitado a: <b>{rereferrals} usuarios</b>
💸 Su saldo: <b>{balance} Sol</b>''',parse_mode="HTML",disable_notification = True)
        except:
            print("Msg send error")
        else:
            print('user not find')

#Устанавливает лимит времени на получение награды
async def update_watching(user_id, duration,queue):
    if queue == 1:
        await collection.update_one({"_id" : user_id},{"$set":{"watching": int(datetime.now().timestamp()) + duration,"queue" : 2}})
    else:
        await collection.update_one({"_id" : user_id},{"$set":{"watching": int(datetime.now().timestamp()) + duration},"$inc":{"queue": 1}})

#Проверка регистрации
async def new_user(user_id):
    r = await collection.find_one({"_id":user_id})
    return(r)
#Проверка на админа
async def isadmin(user_id):
    r = await collection.find_one({"_id": user_id})
    if r != None:
        admin = r.get("isadmin")
        return(admin)
    else:
        return False

#считаем время до обновления и приводим в нужный формат
async def time_view(update_limit,time_now):
    remaining_time = update_limit - time_now 

    # Преобразуем оставшееся время в объект timedelta
    remaining_timedelta = timedelta(seconds=remaining_time)

    # Преобразуем timedelta в объект datetime
    remaining_datetime = datetime(1, 1, 1) + remaining_timedelta

    # Форматируем оставшееся время в часы:минуты:секунды
    formatted_remaining_time = remaining_datetime.strftime("%H:%M:%S")
    return(formatted_remaining_time)

#Проверка баланса и вызов стадий(заявка)
async def proverka_deneg(user_id):
    r = await collection.find_one({"_id" : user_id})
    balance = r.get("balance")
    if balance < 250:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Empezar a ver 📺", callback_data="watch")).add(InlineKeyboardButton(text="invitaa tus amigos",callback_data ='earn_more'))
        await bot.send_message(user_id,text =f'''El saldo mínimo para retirar es  <b>250 Sol</b>
Su saldo: <b>{balance} Sol</b>
Lamentablemente, este límite tuvo que fijarse para no sobrecargar el sistema con retiradas de pequeñas cantidades.''',parse_mode="HTML", reply_markup=markup)
    else:
        await Form.card_number.set()
        await bot.send_message(user_id,text=f"💳 Envíame los datos de tu cuenta <b>%PAYMENTOS%</b> de la que deseas retirar tus saldos",parse_mode="HTML")

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    user_id = message.chat.id
    username = message.chat.username
    #Достаю id
    referr = message.text.split()
    #Проверка новичка
    r = await new_user(user_id)
    if r == None:
        await message.answer("""Nuestra empresa tiene un acuerdo con una agencia de publicidad para promocionar un vídeo en TikTok 📈
 
Por lo tanto, estamos dispuestos a pagar a cada usuario por ver vídeos cortos subidos por este bot.
 
⚠️ Tienes que ver los vídeos para ser recompensado. Los vídeos duran entre 10 y 15 segundos
 
💰 Puedes ganar hasta <b>50 Sol</b> diariamente viendo vídeos
 
Para empezar, pulse el botón "<b>Ver vídeos y ganar dinero 📺</b>".""",parse_mode="HTML",reply_markup=main)
        #Проверка рефера
        if len(referr)==2:
            referr = int(referr[1])
            await add_user(user_id,referr,username)
            await ref(referr)
            r = await collection.find_one({"_id":referr})
            if r !=0 and r!=None:
                rereferr = r.get("referr")
                referr_username = r.get("username")
                await reref(rereferr)
                try:
                    await bot.send_message(channel_log, text = f"👤 @{username}({user_id}) from @{referr_username}", disable_notification =True)
                except:pass
                print(f"new user|{username}|id:{user_id}from {referr}")
            else:  
                try:
                    await bot.send_message(channel_log, text = f"👤 @{username}id:{user_id} from id:{referr} not registred", disable_notification =True)
                except:pass
                print(f"new user|{username}|id:{user_id}from {referr}")
        else: 
            referr = 0
            await add_user(user_id,referr,username)
            await bot.send_message(channel_log, text = f"👤 @{username} {user_id}")
            print(f"new user|id {user_id}")
    else:
        requested = r.get("requested")
        if requested > 0:
            keyboard = main_canal
        else: 
            keyboard = main
        await message.answer("""Nuestra empresa tiene un acuerdo con una agencia de publicidad para promocionar un vídeo en TikTok 📈
 
Por lo tanto, estamos dispuestos a pagar a cada usuario por ver vídeos cortos subidos por este bot.
 
⚠️ Tienes que ver los vídeos para ser recompensado. Los vídeos duran entre 10 y 15 segundos
 
💰 Puedes ganar hasta <b>50 Sol</b> diariamente viendo vídeos
 
Para empezar, pulse el botón "<b>Ver vídeos y ganar dinero 📺</b>".""",parse_mode="HTML",reply_markup=keyboard)


#Обработчик для кнопки "Смотреть видео"
@dp.message_handler(text=['Ver vídeos y ganar dinero 📺'])
async def videos(message:types.Message):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="Empezar a ver 📺", callback_data="watch")
    markup.add(button)

    await message.answer("""Nuestra empresa tiene un contrato con una agencia de publicidad que necesita promocionar vídeos en TikTok 📈

Por lo tanto, estamos dispuestos a pagar a cada uno de nuestros usuarios por ver vídeos cortos enviados por este bot.
 
⚠ Tienes que ver el vídeo hasta el final para conseguir la recompensa. La duración del vídeo es de 10-15 segundos.
 
💰 Cada día puedes ganar hasta <b>50 Sol</b> viendo vídeos
 
Pulse el botón "<b>Empezar a ver 📺</b>" para comenzar.""", parse_mode="HTML", reply_markup=markup)
     
#Обработчик для кнопки "Canal"
@dp.message_handler(text=['Canal'])
async def canal(message:types.Message):
    user_id = message.chat.id
    metadata =  await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
    link = metadata.get("link")
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Canal',url=link))
    await bot.send_message(user_id, text='Únete a nuestro canal y te enseñaremos a ganar dinero!',reply_markup=markup)

#Обработчик для кнопки "Правила"
@dp.message_handler(text=['Reglas 🎯'])
async def rules(message:types.Message):
    await message.answer("""Nuestra empresa tiene un acuerdo con una agencia de publicidad para promocionar un vídeo en TikTok 📈
 
Por lo tanto, estamos dispuestos a pagar a cada usuario por ver vídeos cortos subidos por este bot.
 
⚠️ Tienes que ver los vídeos para ser recompensado. Los vídeos duran entre 10 y 15 segundos
 
💰 Puedes ganar hasta <b>50 Sol</b> diariamente viendo vídeos
 
Para empezar, pulse el botón "<b>Ver vídeos y ganar dinero 📺</b>".""",parse_mode="HTML")
    
#ОБработчик для кнопки "Профиль"
@dp.message_handler(text=['📱 Mi perfil'])
async def profile(message: types.Message):
    user_id = message.chat.id
    r = await collection.find_one({"_id":user_id})
    balance = r.get("balance")
    referrals = r.get("referrals")
    rereferrals = r.get("rereferrals")
    await message.answer(f"""Su saldo: <b>{balance} Sol</b>
Número de amigos invitados: <b>{referrals}</b>
Usuarios invitados por tus amigos: <b>{rereferrals}</b>""",parse_mode="HTML")




#ОБработчик ля кнопки "Вывод"
@dp.message_handler(text=['Retirada de dinero  🏧'])
async def withdraw(message:types.Message):

    
    user_id= message.chat.id
    r = await collection.find_one({"_id":user_id})
    requested = r.get("requested")
    if requested == 1:
        requested_time = r.get("requested_time")
        time_now = int(datetime.now().timestamp())
        if time_now-requested_time <60*60*48:

            await bot.send_message(user_id,text=f'''Con éxito ✅ 
Su solicitud ha sido enviada ✅ 
Espere 48 horas para una respuesta''')
        else:
            await bot.send_message(user_id,text=f'''Desafortunadamente, experimentamos problemas técnicos,
¡nos disculpamos!
Su dinero será acreditado a su cuenta dentro de las 72 horas''')
        return
    
    metadata =  await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
    link = metadata.get("link")
    markup1 = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Empezar a ver 📺", callback_data="watch"))
    markup2 = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Únase al canal", url=link)).add(InlineKeyboardButton(text="comprobar las incripciones",callback_data='verify_member'))
    
    watched_videos = r.get("watched_videos")
    # Получаем информацию о пользователе как участнике чата (канала)
    ismember = r.get("ismember")

    if watched_videos< 5:
        await message.answer("""❗️ Debes ver al menos 5 vídeos para retirar fondos.

Haz clic en Empezar a ver 📺 y empieza ya.""", reply_markup=markup1)
    else:
        if ismember == 0:
            await message.answer(f"""{ad_msg_withdraw}""",reply_markup=markup2)
        else: 
            await proverka_deneg(user_id)

# Обработчик команды или кнопки "exit"
@dp.callback_query_handler(lambda c: c.data == "exit",state="*")
async def exit_state(call: types.CallbackQuery, state: FSMContext):

    await state.finish()  # Завершение текущего состояния
    await bot.delete_message(call.message.chat.id,call.message.message_id)
    await bot.send_message(call.message.chat.id, text='no olvides aplicar',reply_markup=main)



@dp.callback_query_handler(lambda c: c.data == "verify_member")
async def verify_member(call: types.CallbackQuery):
    user_id = call.message.chat.id
    r =  await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
    channel_id = r.get("channel_id")
    chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

    if chat_member.status == "member" or chat_member.status == "administrator" or chat_member.status == "creator":
        await bot.send_message(user_id,text ='''Te has suscrito con éxito al canal ✅.
No es necesario que se dé de baja del canal si quiere retirar dinero.''')
        await collection.update_one({"_id" : user_id},{"$set":{"ismember":1}})
        await proverka_deneg(user_id)
    else:
       
        r =  await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
        link = r.get("link")
        await bot.delete_message(user_id,call.message.message_id)
        markup2 = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Únase al canal", url=link)).add(InlineKeyboardButton(text="comprobar las incripciones",callback_data='verify_member'))
        await bot.send_message(user_id,text="Todavía no estás suscrito al canal",reply_markup=markup2)

#Обработчик для кнопки "Зарабоать еще больше"
@dp.message_handler(text=['💰 Ganar aún más dinero 💰'])
async def earn_more(message: types.Message):
    await message.answer(f"""Nuestro proyecto es nuevo en telegram y necesitamos que todo el mundo nos conozca, por lo que estamos dispuestos a pagar por la publicidad 💵
 
🏆 Esta es tu link de enlace para las invitaciones 👇
 
https://t.me/TT_earnbot?start={message.chat.id}
 
✅ Copia el enlace y envíalo a tus amigos y conocidos
 
🏆 Por cada persona que visite el bot a través de tu enlace, obtienes <b>5 Sol</b>
 
Si alguien a quien invitas invita a nuevas personas, te pagan por usuario <b>2.5 Sol</b> 
 
Así que puedes ganar sin límites!""",parse_mode="HTML")
    
@dp.message_handler(commands=['set_admin'])
async def set_admin(message: types.Message):
    user_id = message.chat.id
    try:
        if message.text =='/set_admin':
            await message.reply("Empty request. \nExample: \"/set_admin durov\"\n!username must be registered here!")
        else:
            username= message.text.split()[1]
        
            admin= await isadmin(user_id)
            if admin ==1:
                r = await collection.update_one({"username":username},{"$set":{"isadmin":1}})
                if r.matched_count>0:
                    await message.reply(f"{username} is admin now 😎😎😎")
                else:
                    await message.reply("🤡user not registred")
            else:
                await message.reply("🤡who are you")
    except:
        await message.reply("🤡user not registred")

@dp.message_handler(commands=['all_videos'])
async def all_videos(message: types.Message):
    user_id = message.chat.id
    admin = await isadmin(user_id)
    if admin == 1:
        all_videos = await video_collection.find().to_list(None)
        for video in all_videos:
            delete_callback_data = f"delete_video_{video['file_name']}"
            markup = InlineKeyboardMarkup()
            button1 = InlineKeyboardButton(text="❌Delete❌", callback_data=delete_callback_data)
            markup.add(button1)
            file_name = video["file_name"]
            await bot.send_video(chat_id=message.chat.id, video=video["_id"], caption=file_name,reply_markup=markup)
            #Баг возможно нужен тайм слип
    else:
        await message.answer("🤡🤡🤡")

# Регистрируем обработчик колбека delete_callback_data
@dp.callback_query_handler(lambda c: c.data.startswith('delete_video'))
async def delete_video_callback_handler(callback_query: types.CallbackQuery):
    r = await handle_delete_callback(callback_query)
    if r:
         await bot.answer_callback_query(callback_query.id, text="Deleted", show_alert=False)
         await bot.delete_message(callback_query.message.chat.id,callback_query.message.message_id)
         await set_videos()
    else:
        await bot.answer_callback_query(callback_query.id, text="Something went wrong", show_alert=False)

# Обработчик колбека для кнопки DELETE
async def handle_delete_callback(callback_query: types.CallbackQuery):
    data = callback_query.data  # Получаем идентификатор видео из колбека
    file_name = data.split("delete_video_")[1]

    # Здесь код для удаления видео с использованием file_name
    r = await video_collection.delete_one({"file_name": file_name})
    if r.deleted_count == 1:
        return True
    else:
        return False
            
@dp.message_handler(commands=['set_videos'])
async def set_videos():
    # Получение всех документов из коллекции
    all_videos = await video_collection.find().to_list(None)
    # Вывод списка всех документов
    i=0
    for video in all_videos:
        i+=1
        await video_collection.update_one({"_id": video["_id"]}, {"$set": {"queue" : i}})
    # await message.answer("👍🏿queue has been updated")

@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    user_id = message.chat.id
    admin = await isadmin(user_id)
    if admin == 1:
        await bot.send_message(user_id,"""📌Admin Panel📌:

/ad - RASSILKA
/admin_help - this page                              
/all_videos - deleting here too
/set_video - after adding and deleting videos you need to reload the queue with this command
/set_admin - makes user into admin. example: "/set_admin durov"        
/stats
/member - Настройка рекламного канала. 
/start - swith to user panel """,reply_markup=admin_main)
    else:
        await message.answer("🤡🤡🤡")

@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    total_count = await collection.count_documents({})
    await message.answer(f"Registred users: {total_count}")



# Обработчик для вызова видео (первое без мануала)
@dp.callback_query_handler(lambda c: c.data == "watch")
async def watch(call: types.callback_query):
    
    #Проверка в монго дб
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="Participar (recibir un premio)", callback_data="receive")
    markup.add(button1)
    
    user_id = call.message.chat.id
    r = await collection.find_one({"_id":user_id})
    queue = r.get("queue")
    r = await video_collection.find_one({"queue": queue})
    if r!=None:
        video_id = r.get("_id")
        duration = r.get('duration') 
        await bot.send_video(chat_id=user_id, video = video_id,reply_markup=markup)
        await update_watching(user_id,duration,queue)
    else:
        queue = 1
        r = await video_collection.find_one({"queue": queue})
        video_id = r.get("_id")
        duration = r.get('duration') 
        await bot.send_video(chat_id=user_id, video = video_id,reply_markup=markup)
        await update_watching(user_id,duration,queue)
    
# Обработчик для инлайн кнопки "Получить награду" 
@dp.callback_query_handler(lambda c: c.data == "receive")
async def receive(call: types.CallbackQuery):
    user_id = call.message.chat.id
    #Проверка в монго дб
    r = await collection.find_one({"_id":user_id})
    update_limit= r.get("update_limit")
    time_now= int(datetime.now().timestamp())
    if update_limit < time_now and update_limit !=0:
        await collection.update_one({"_id":user_id},{"$set":{"today_left": 20}})
    r = await collection.find_one({"_id":user_id})
    watching = r.get("watching")
    balance = r.get("balance")
    update_limit= r.get("update_limit")
    today_left = r.get("today_left")
    hold = 60*60*8
    if today_left>0:
        if int(watching) < time_now:
            #Если начал смотреть, то рефреш времени будет через 8 часов.
            if today_left ==20:
                await collection.update_one({"_id":user_id},{"$inc":{"balance":2.5, "today_left": -1,"watched_videos":1},
                                                             "$set":{"update_limit": time_now + hold}})
            else:
                await collection.update_one({"_id":user_id},{"$inc":{"balance":2.5, "today_left": -1,"watched_videos":1}})
            await bot.send_message(user_id, f"""🎉 Has ganado <b>2.5 Sol</b> por ver el vídeo.\n                    
🤑 Su saldo: <b>{balance+2.5} Sol</b>""",parse_mode="HTML")
            await bot.delete_message(call.message.chat.id,call.message.message_id)
        else:
            await bot.answer_callback_query(call.id,"""⚠️Tienes que ver el vídeo en su totalidad⚠️""")
            await bot.delete_message(call.message.chat.id,call.message.message_id)
            #Следующее видео вызывается отдельной функцией, а не предыдущей, для добавления инлайн кнопки мануала
        await receive_watch(call)
    else:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text="💰 Ganar aún más dinero 💰", callback_data ='earn_more'))
        time_left = await time_view(update_limit=update_limit,time_now=time_now)
        await bot.send_message(user_id, text=f'''⚠️ Hoy has cumplido con todos tus compromisos publicitarios y has recibido un premio! 😌

Puedes conseguir un nuevo contrato de publicidad durante: <b>{time_left}</b>

Si quieres ganar más, haz clic en el botón de abajo 👇''', parse_mode="HTML", reply_markup=markup) 
        await bot.delete_message(call.message.chat.id,call.message.message_id)


# Обработчик для вызова видео (предлагается мануал)
@dp.callback_query_handler(lambda c: c.data == "receive_watch")
async def receive_watch(call: types.callback_query):

    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="Participar (recibir un premio)", callback_data="receive")
    button2 = InlineKeyboardButton(text="💰 Ganar aún más dinero 💰", callback_data ='earn_more')
    markup.add(button1).add(button2)
    
    user_id = call.message.chat.id
    r = await collection.find_one({"_id":user_id})
    queue = r.get("queue")
    r = await video_collection.find_one({"queue": queue})
    if r!=None:
        video_id = r.get("_id")
        duration = r.get('duration') 
        await bot.send_video(chat_id=user_id, video = video_id,reply_markup=markup)
        await update_watching(user_id,duration,queue)
    else:
        queue = 1
        r = await video_collection.find_one({"queue": queue})
        video_id = r.get("_id")
        duration = r.get('duration') 
        await bot.send_video(chat_id=user_id, video = video_id,reply_markup=markup)
        await update_watching(user_id,duration,queue)

# Обработчик для вызова обработчика "Заработать еще больше"
@dp.callback_query_handler(lambda c: c.data == "earn_more")
async def call_witchdraw(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await earn_more(call.message)

#Рекланые посты 
@dp.message_handler(content_types=types.ContentType.ANY, is_forwarded=True)
async def forward_handler(message: types.Message):
    admin = message.from_user.id

    # Проверяем, является ли отправитель администратором
    is_admin = await isadmin(admin)
    if is_admin == 0 or is_admin == False:
        await message.reply("Вы не являетесь администратором!")
        return
    
    # Получаем информацию о пересланном сообщении
    forwarded_message = message
    if forwarded_message:
        await handle_send_ad(forwarded_message,admin=admin)
         

async def handle_send_ad(forwarded_message: types.Message, admin):
    content_type = forwarded_message.content_type

    r = await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
    state = r.get("state")
    if state==0:
        user_ids = await collection.distinct("_id")
    elif state==1:
        user_ids = [admin]
    else: 
        admin_users_cursor =  collection.find({"isadmin": 1})
        user_ids = [document["_id"] async for document in admin_users_cursor]

    i=0
    text = forwarded_message.html_text
    
    if content_type == types.ContentType.TEXT:
        text = forwarded_message.html_text
        photo_id = None
        video_id = None
        animation_id = None

        # Проверяем наличие фото в пересланном сообщении
        if forwarded_message['photo']!=[]:
            photo_id = forwarded_message.photo.file_id[-1]
        elif forwarded_message['video']:
            video_id = forwarded_message.video.file_id
        elif forwarded_message['animation']:
            animation_id = forwarded_message.animation.file_id

        for user_id in user_ids:
            try:
                if photo_id:
                    await bot.send_photo(user_id, photo=photo_id, caption=text, parse_mode="HTML")
                elif video_id:
                    await bot.send_video(user_id, video=video_id, caption=text,parse_mode="HTML")
                elif animation_id:
                    await bot.send_animation(user_id, animation=animation_id, caption=text,parse_mode="HTML")
                else:
                    await bot.send_message(user_id, text, parse_mode="HTML")
                await asyncio.sleep(1)  # Пауза между сообщениями
                i+=1
            except:pass

    elif content_type == types.ContentType.PHOTO:
        for user_id in user_ids:
            try:
                if forwarded_message.caption:
                    await bot.send_photo(user_id,photo=forwarded_message.photo[-1].file_id, caption=forwarded_message.html_text,parse_mode="HTML")
                else:
                    await bot.send_photo(user_id,photo=forwarded_message.photo[-1].file_id, )
                i+=1
            except: pass
            await asyncio.sleep(1)
    elif content_type == types.ContentType.VIDEO:
        for user_id in user_ids:
            try:
                if forwarded_message.caption:
                    await bot.send_video(user_id, video=forwarded_message.video.file_id, caption=forwarded_message.html_text,parse_mode="HTML")
                else:
                    await bot.send_video(user_id, video=forwarded_message.video.file_id)
                i+=1
            except: pass
            await asyncio.sleep(1)
    elif content_type == types.ContentType.ANIMATION:
        for user_id in user_ids:
            try:
                if forwarded_message.caption:
                    await bot.send_animation(user_id, animation=forwarded_message.animation.file_id, caption=forwarded_message.html_text,parse_mode="HTML")
                else:
                    await bot.send_animation(user_id, animation=forwarded_message.animation.file_id) 
                i+=1
            except: pass
            await asyncio.sleep(1) 
    await bot.send_message(channel_log,text=f"Messages sent: <b>{i}</b>\nSender: <b>{admin}</b>\nstate={state}(0-all,1-test,2-admins)",parse_mode="HTML",disable_notification=True)

#Добавление видиков. стоит вконце чтобы не попадать под рекламные посты
@dp.message_handler(content_types=types.ContentType.VIDEO)
async def handle_video(message: types.Message):
    user_id= message.chat.id
    admin = await isadmin(user_id)
    if admin ==1:
        max_video_size = 10 * 1024 * 1024  # Максимальный размер видео (10 МБ)
        if message.video.file_size > max_video_size:
            await message.reply("🙄The video is too big. The maximum size is 10 MB.")
            return
       
        
        existing_document = await video_collection.find_one({"file_name": message.video.file_name})
        
        if existing_document and existing_document.get("file_name")!=None:
            await message.reply("already exists")
        else:
            # Создаем объект для добавления нового документа
            video_data = {
            "_id": message.video.file_id,
            "duration": message.video.duration,
            "file_name": message.video.file_name,
            "queue": 0
            }
            await video_collection.insert_one(video_data)
            await message.reply("👍🏿 Video successfully added!")
            await set_videos()
        # Проверка результата обновления или вставки
    else:
        await message.reply("🤡")

@dp.message_handler(commands=['member'])
async def member(message: types.Message):
    await message.answer(f"""Команды:\n
/set_link - устанавливает ссылку на паблик в кнопку
Пример: /set_link https://t.me/+ajDEWo8xZW9jM2E3
Без аргумента вернет текущее значение
                         
/set_channel_id - установит Id канала для проверки подписки
Пример(публичный канал): /set_channel_id @durov
Пример(закрытый канал): /set_channel_id -1001006503122
Чтобы получить id закрытого канала перешли из него любой пост боту @username_to_id_bot. 
В обоих случаях необходимо выдать админку боту в канале, канал/добавить юзера/ пишем имя бота/ появляется кнопка сделать админом/ все галочки можно снять
Без аргумента вернет текущее значение""")
    
@dp.message_handler(commands=['ad'])
async def ad(message: types.Message):
    user_id = message.chat.id
    admin = await isadmin(user_id)
    if admin == 1:
        r = await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
        state = r.get("state")
        if state == 0:
            state_='all'
        elif state ==1:
            state_ ='test'
        else:
            state_ = 'admins'
        markup = InlineKeyboardMarkup()
        btn_all =InlineKeyboardButton(text ='all',callback_data="set_state0")
        btn_test =InlineKeyboardButton(text ='test',callback_data="set_state1")
        btn_admins =InlineKeyboardButton(text ='admins',callback_data="set_state2")
        markup.row(btn_all,btn_test,btn_admins)

        await bot.send_message(user_id, text=f"""Отправка рекламного поста:
Если переслать боту сообщение и другого чата (должно быть помечено как пересланное сообщение (forwarded message))
Есть 3 режима отправки. В каком режиме сейчас бот, туда и отправятся:
"all" - отправить всем 
"test" - отправить себе тестовое
"admins" - отправить админам      
Сейчас установлен: <b>{state_}</b>                                                        

UPD: На данный момент бот может переслать текст, видео, фото, гиф. Несколько медиафайлов сразу бот не умеет. А надо ли? 
Пока бот занят рассылкой, остальные функции могут быть замедлены.
Результат отправки чекаем тут: https://t.me/ttbot_stats_log""",parse_mode="HTML", reply_markup=markup)
    else:

        await message.answer("🤡🤡🤡")

# Регистрируем обработчик колбека set_state
@dp.callback_query_handler(lambda c: c.data.startswith('set_state'))
async def set_state_callback_handler(callback_query: types.CallbackQuery):
    r = await handle_set_state(callback_query)
    if r:
         await bot.answer_callback_query(callback_query.id, text="✅successfully✅", show_alert=False)
    else:
        await bot.answer_callback_query(callback_query.id, text="Something went wrong", show_alert=False)

@dp.message_handler(lambda message: message.text.startswith('/set_link'))
async def set_link(message: types.Message):
    try:
        link = message.text.split()[1]
        r = await metadata_collection.update_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")},{"$set": {"link": link}})
        if r.matched_count >0:
            await message.answer('✅')
        else:
            await message.answer('Error...')
    except:
        r = await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
        link = r.get("link")
        await message.reply(text=f"link = {link}")

@dp.message_handler(lambda message: message.text.startswith('/set_channel_id'))
async def set_channel_id(message: types.Message):
    try:
        channel_id = message.text.split()[1]
        r = await metadata_collection.update_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")},{"$set": {"channel_id": channel_id}})
        if r.matched_count >0:
            await message.answer('✅')
        else:
            await message.answer('Error...')
    except:
        r = await metadata_collection.find_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")})
        channel_id = r.get("channel_id")
        await message.reply(text=f"channel_id = {channel_id}")

# Обработчик колбека для кнопки set_state
async def handle_set_state(callback_query: types.CallbackQuery):
    data = callback_query.data  
    state = int(data.split("set_state")[1])
    r = await metadata_collection.update_one({"_id": ObjectId("64d2c5a934ced84d95b898c0")},{"$set": {"state": state}})

    if r.matched_count >0:
        return True
    else:
        return False
 
# Обработка сообщений в состоянии card_number)
@dp.message_handler(state=Form.card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = message.text
        
    await collection.update_one({"_id":user_id},{"$set": {"card_number": data}})
    await Form.email.set()
    await bot.send_message(user_id, text=f'''Introduzca su dirección de correo electrónico y le enviaremos la información.
por ejemplo: <a href="amigobro@gmail.com">amigobro@gmail.com</a>''', parse_mode="HTML")

# Обработка сообщений в состоянии email)
@dp.message_handler(state=Form.email)
async def process_email(message: types.Message,state: FSMContext):
    user_id = message.from_user.id
    data = message.text
    email = await is_valid_email(data)
    if not email:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text='salir ↩️', callback_data="exit"))
        await bot.send_message(user_id, text=f'''Introduzca su dirección de correo electrónico y le enviaremos la información.
por ejemplo: <a href="amigobro@gmail.com">amigobro@gmail.com</a>''', parse_mode="HTML", reply_markup=markup)
        return
    
    await collection.update_one({"_id":user_id},{"$set": {"email": data}})
    await Form.amount.set()
    r = await collection.find_one({"_id":user_id})
    balance = r.get("balance")

    await bot.send_message(user_id, text=f'''Introduzca el importe que desea retirar.

El importe mínimo de retirada es <b>250 Sol</b>.

💵 Su saldo <b>%CURRENCIA% {balance}</b>''', parse_mode="HTML")

# Обработка сообщений в состоянии amount)
@dp.message_handler(state=Form.amount)
async def process_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = message.text
    r = await collection.find_one({"_id":user_id})
    balance = r.get("balance")
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text='salir ↩️', callback_data="exit"))

    try:
        currency = int(float(data))
        if  currency< 250 or currency>balance:
            await bot.send_message(user_id, text=f'''❌  No hay fondos suficientes en su saldo.El importe mínimo de retirada es <b>250 Sol</b>.

    💵 Your balance <b>%CURRENCY% {balance}</b>''',parse_mode="HTML",reply_markup=markup)
            return
    except: #обработчик исключения если строка не является числом.
        await bot.send_message(user_id, text=f'''❌  Ingrese solo números.El importe mínimo de retirada es <b>250 Sol</b>.

💵 Your balance <b>%CURRENCY% {balance}</b>''',parse_mode="HTML",reply_markup=markup)
        return
    time_now = int(datetime.now().timestamp())
    await collection.update_one({"_id":user_id},{"$set":{"requested" :1,"requested_time":time_now}})
         ###СМЕНА КЛАВЫ
    await bot.send_message(user_id, text=f'''Con éxito ✅ 
Su solicitud ha sido enviada ✅ 
Espere 48 horas para una respuesta''',reply_markup=main_canal)
    
    await collection.update_one({"_id":user_id},{"$set": {"requested_amount": int(data)}})
    await state.reset_state()


executor.start_polling(dp)
