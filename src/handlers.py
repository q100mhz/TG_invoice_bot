import os
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from src.database import save_profile, get_profile, create_invoice_entry
from src.pdf_generator import create_invoice_pdf

router = Router()

class SetupProfile(StatesGroup):
    company_name = State()
    inn = State()
    bank_name = State()
    bik = State()
    rs = State()
    ks = State()

class CreateInvoice(StatesGroup):
    buyer_name = State()
    item_name = State()
    price = State()

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Создать счет")],
            [KeyboardButton(text="⚙️ Мои реквизиты")]
        ],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"Получена команда /start от {message.from_user.id}")
    await state.clear()
    profile = get_profile(message.from_user.id)
    if not profile:
        await message.answer(
            "👋 Привет! Я бот для генерации счетов на оплату в PDF.\n\n"
            "Для начала работы давайте один раз сохраним ваши реквизиты.\n"
            "Введите **название вашей организации/ИП** (например: `ИП Иванов Иван Иванович`):"
        )
        await state.set_state(SetupProfile.company_name)
    else:
        await message.answer(
            f"С возвращением, {profile['company_name']}!\nВыберите действие в меню:",
            reply_markup=main_kb()
        )

@router.message(SetupProfile.company_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text.strip())
    await message.answer("Введите ваш **ИНН**:")
    await state.set_state(SetupProfile.inn)

@router.message(SetupProfile.inn)
async def process_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text.strip())
    await message.answer("Введите **наименование вашего банка** (например: `АО ТИНЬКОФФ БАНК`):")
    await state.set_state(SetupProfile.bank_name)

@router.message(SetupProfile.bank_name)
async def process_bank(message: Message, state: FSMContext):
    await state.update_data(bank_name=message.text.strip())
    await message.answer("Введите **БИК банка** (9 цифр):")
    await state.set_state(SetupProfile.bik)

@router.message(SetupProfile.bik)
async def process_bik(message: Message, state: FSMContext):
    await state.update_data(bik=message.text.strip())
    await message.answer("Введите ваш **расчетный счет (р/с)** (20 цифр):")
    await state.set_state(SetupProfile.rs)

@router.message(SetupProfile.rs)
async def process_rs(message: Message, state: FSMContext):
    await state.update_data(rs=message.text.strip())
    await message.answer("Введите **корреспондентский счет банка (к/с)** (20 цифр):")
    await state.set_state(SetupProfile.ks)

@router.message(SetupProfile.ks)
async def process_ks(message: Message, state: FSMContext):
    data = await state.get_data()
    save_profile(
        user_id=message.from_user.id,
        company_name=data['company_name'],
        inn=data['inn'],
        bank_name=data['bank_name'],
        bik=data['bik'],
        rs=data['rs'],
        ks=message.text.strip()
    )
    await state.clear()
    await message.answer("✅ Реквизиты успешно сохранены! Теперь вы можете выставлять счета.", reply_markup=main_kb())

@router.message(F.text == "⚙️ Мои реквизиты")
async def show_profile(message: Message, state: FSMContext):
    profile = get_profile(message.from_user.id)
    if not profile:
        await cmd_start(message, state)
        return
    text = (
        f"🏢 **{profile['company_name']}**\n"
        f"ИНН: `{profile['inn']}`\n"
        f"Банк: {profile['bank_name']}\n"
        f"БИК: `{profile['bik']}`\n"
        f"Р/с: `{profile['rs']}`\n"
        f"К/с: `{profile['ks']}`\n\n"
        "Чтобы изменить, отправьте команду /settings"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("settings"))
async def reset_profile(message: Message, state: FSMContext):
    await message.answer("Введите **название вашей организации/ИП**:")
    await state.set_state(SetupProfile.company_name)

@router.message(F.text == "📄 Создать счет")
async def start_invoice(message: Message, state: FSMContext):
    profile = get_profile(message.from_user.id)
    if not profile:
        await message.answer("Сначала заполните реквизиты!")
        await cmd_start(message, state)
        return
    await message.answer("Введите **название клиента / покупателя** (например: `ООО Вектор`):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CreateInvoice.buyer_name)

@router.message(CreateInvoice.buyer_name)
async def process_buyer(message: Message, state: FSMContext):
    await state.update_data(buyer_name=message.text.strip())
    await message.answer("Введите **наименование услуги или товара** (например: `Разработка бота`):")
    await state.set_state(CreateInvoice.item_name)

@router.message(CreateInvoice.item_name)
async def process_item(message: Message, state: FSMContext):
    await state.update_data(item_name=message.text.strip())
    await message.answer("Введите **сумму к оплате** в рублях (например: `15000`):")
    await state.set_state(CreateInvoice.price)

@router.message(CreateInvoice.price)
async def process_price(message: Message, state: FSMContext):
    price_text = message.text.replace(" ", "").replace(",", ".")
    try:
        price = float(price_text)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например `25000`):")
        return
    
    data = await state.get_data()
    seller = get_profile(message.from_user.id)
    invoice_num = create_invoice_entry(message.from_user.id)
    
    os.makedirs("invoices", exist_ok=True)
    pdf_filename = f"invoices/invoice_{invoice_num}_{message.from_user.id}.pdf"
    
    await message.answer("⏳ Генерирую счет в PDF...")
    
    try:
        create_invoice_pdf(
            seller=seller,
            buyer_name=data['buyer_name'],
            item_name=data['item_name'],
            price=price,
            invoice_num=invoice_num,
            output_path=pdf_filename
        )
        
        pdf_file = FSInputFile(pdf_filename, filename=f"Счет_{invoice_num}.pdf")
        await message.answer_document(
            document=pdf_file,
            caption=f"✅ Счет №{invoice_num} на сумму {price:,.2f} ₽ готов!",
            reply_markup=main_kb()
        )
    finally:
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        await state.clear()