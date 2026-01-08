from aiogram import Router, F
from aiogram.filters import Command
import logging
from keyboard.keyboard import (
    quote_menu,
    quote_tickers_by_area,
    asset_type,
    quote_view,
    config_table,
    config_chart,
    technical_analysis_menu,
    back_button,
    loading_keyboard
)
from lexicon.lexicon import SECTORS, CHART_PERIODS, CHART_TYPES
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from services.quote_service import QuoteService, CompanyInfo, StockData

quote_router = Router()
logger = logging.getLogger(__name__)
quote_service = QuoteService()

@quote_router.message(Command("quote"))
async def start_quote_nav(message: Message):
    await message.answer(
        "📊 <b>Котировки и графики</b>\n\n"
        "Выберите интересующую вас сферу экономики:",
        reply_markup=quote_menu(),
        parse_mode="HTML"
    )

@quote_router.callback_query(F.data.startswith("sector_"))
async def handle_sector_selection(callback: CallbackQuery):
    try:
        data = callback.data
        logger.info(f"Выбор сектора: {data}")
        clean_data = data.replace("sector_", "")
        parts = clean_data.split("_")
        
        if len(parts) == 1:
            sector_id = parts[0]
            page = 1
        elif len(parts) == 2:
            sector_id = parts[0]
            try:
                page = int(parts[1])
            except ValueError:
                logger.error(f"Не могу преобразовать '{parts[1]}' в число")
                page = 1
        else:
            logger.error(f"Неизвестный формат: {data}")
            await callback.answer("Ошибка формата данных")
            return
        
        sector_name = SECTORS.get(sector_id, sector_id.replace("_", " ").title())
        
        logger.info(f"Сектор: {sector_id}, Страница: {page}")
        
        if sector_id not in SECTORS:
            logger.error(f"Сектор '{sector_id}' не найден")
            await callback.answer("Ошибка: сектор не найден")
            return

        tickers, total_pages = await quote_service.get_tickers_by_sector(sector_id, page)
        
        logger.info(f"Получено тикеров: {len(tickers)}")
        
        if not tickers:
            await callback.message.answer(
                f"📊 <b>{sector_name}</b>\n\n"
                "❌ <b>Нет доступных тикеров в этой сфере</b>\n\n"
                "<i>Попробуйте выбрать другой сектор</i>",
                reply_markup=back_button("back_to_sectors"),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        await callback.message.answer(
            f"📊 <b>{sector_name}</b>\n\n"
            f"Выберите компанию для просмотра:",
            reply_markup=quote_tickers_by_area(sector_id, tickers, page, total_pages),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_sector_selection: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте снова")

@quote_router.callback_query(F.data.startswith("ticker_"))
async def handle_ticker_selection(callback: CallbackQuery):
    try:
        ticker = callback.data.replace("ticker_", "")
        logger.info(f"Выбор тикера: {ticker}")
        
        company_info = await quote_service.get_company_info(ticker)
        
        if company_info:
            message_text = await quote_service.format_company_message(company_info)
            message_text += "\n\n👇 <b>Выберите тип актива:</b>"
        else:
            message_text = f"""
📊 <b>{ticker}</b>

<i>Информация о компании временно недоступна</i>

👇 <b>Выберите тип актива для просмотра:</b>
"""
        
        await callback.message.answer(
            message_text,
            reply_markup=asset_type(ticker),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_ticker_selection: {e}")
        await callback.answer("Ошибка загрузки данных")

@quote_router.callback_query(F.data.startswith("asset_"))
async def handle_asset_type_selection(callback: CallbackQuery):
    try:
        data = callback.data.replace("asset_", "")
        asset_type_str, ticker = data.split("_", 1)
        logger.info(f"Выбор типа актива: {ticker} - {asset_type_str}")
        
        if asset_type_str == "stocks":
            stock_data = await quote_service.get_stock_data(ticker)
            
            if stock_data:
                company_info = await quote_service.get_company_info(ticker)
                company_name = company_info.name if company_info else ticker
                
                message_text = await quote_service.format_stock_message(
                    ticker, company_name, stock_data
                )
            else:
                message_text = f"""
📊 <b>{ticker} - Акции</b>

❌ <i>Не удалось загрузить данные по акциям</i>
"""
        
        elif asset_type_str == "bonds":
            bond_data = await quote_service.get_bond_data(ticker)
            
            if bond_data:
                message_text = await quote_service.format_bond_message(ticker, bond_data)
            else:
                message_text = f"""
📊 <b>{ticker} - Облигации</b>

❌ <i>Не удалось загрузить данные по облигациям</i>
"""
        
        else:
            message_text = f"""
📊 <b>{ticker} - {asset_type_str.capitalize()}</b>

💸 <i>Данные временно недоступны</i>
"""
        
        message_text += "\n\n👇 <b>Выберите режим просмотра:</b>"
        
        await callback.message.answer(
            message_text,
            reply_markup=quote_view(ticker, asset_type_str),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_asset_type_selection: {e}")
        await callback.answer("Ошибка загрузки данных")

@quote_router.callback_query(F.data.startswith("table_"))
async def show_table(callback: CallbackQuery):
    try:
        data = callback.data.replace("table_", "")
        
        if data.startswith("auto_"):
            ticker_asset = data.replace("auto_", "")
            ticker, asset_type = ticker_asset.split("_", 1)
            await callback.answer("🔄 Автообновление включено")
        
        elif data.startswith("sort_"):
            sort_data = data.replace("sort_", "")
            sort_type, ticker, asset_type = sort_data.split("_", 2)
            await callback.answer(f"Сортировка по {sort_type}")
        
        else:
            ticker, asset_type = data.split("_", 1)
        
        trades = await quote_service.get_trade_history(ticker, asset_type, 15)
        
        if trades:
            table_html = await quote_service.format_trade_table(trades)
            
            await callback.message.answer(
                table_html,
                reply_markup=config_table(ticker, asset_type),
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                f"📋 <b>Таблица торгов: {ticker}</b>\n\n"
                "<i>История торгов временно недоступна</i>\n"
                "<i>Данные обновляются в рабочее время биржи</i>",
                reply_markup=loading_keyboard(),
                parse_mode="HTML"
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_table: {e}")
        await callback.answer("Ошибка загрузки таблицы")

@quote_router.callback_query(F.data.startswith("chart_"))
async def show_chart(callback: CallbackQuery):
    try:
        data = callback.data.replace("chart_", "")
        
        if data.startswith("type_"):
            chart_data = data.replace("type_", "")
            ticker, asset_type, chart_type = chart_data.split("_", 2)
            
            chart_name = CHART_TYPES.get(chart_type, chart_type)
            await callback.answer(f"Тип графика: {chart_name}")
            
            await callback.message.answer(
                f"📈 <b>Настройка графика: {ticker}</b>\n\n"
                f"Выбран тип: {chart_name}\n"
                "Выберите период:",
                reply_markup=config_chart(ticker, asset_type),
                parse_mode="HTML"
            )
            return
        
        parts = data.split("_")
        if len(parts) >= 3:
            ticker, asset_type, period = parts[0], parts[1], parts[2]
            period_name = CHART_PERIODS.get(period, period)
            
            loading_msg = await callback.message.answer(
                f"📈 <b>Генерация графика...</b>\n\n"
                f"<i>{ticker} - {period_name}</i>",
                parse_mode="HTML"
            )
            
            try:
                chart_type = "candle"
                if len(parts) == 4:
                    chart_type = parts[3] if parts[3] in ["line", "candle", "bar"] else "candle"
                
                chart_image = await quote_service.generate_chart(
                    ticker, asset_type, period, chart_type
                )
                
                if chart_image:
                    image_file = BufferedInputFile(
                        chart_image,
                        filename=f"{ticker}_{period}.png"
                    )
                    
                    await callback.message.answer_photo(
                        photo=image_file,
                        caption=f"📈 <b>{ticker}</b> - {period_name}\n"
                               f"💼 <i>Тип: {asset_type}</i>",
                        parse_mode="HTML"
                    )
                    await loading_msg.delete()
                else:
                    await loading_msg.edit_text(
                        f"❌ <b>Не удалось сгенерировать график</b>\n\n"
                        f"<i>Графики временно недоступны</i>\n"
                        f"<i>Функция в разработке</i>",
                        parse_mode="HTML"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка генерации графика: {e}")
                await loading_msg.edit_text(
                    f"❌ <b>Ошибка при генерации графика</b>\n\n"
                    f"<i>Попробуйте позже</i>",
                    parse_mode="HTML"
                )
            
            await callback.answer(f"График {ticker} за {period_name}")
            
    except Exception as e:
        logger.error(f"Ошибка в show_chart: {e}")
        await callback.answer("Ошибка генерации графика")

@quote_router.callback_query(F.data.startswith("back_"))
async def handle_back_navigation(callback: CallbackQuery):
    try:
        back_data = callback.data
        logger.info(f"Навигация назад: {back_data}")
        
        if back_data == "back_to_sectors":
            await start_quote_nav(callback.message)
        
        elif back_data == "back_to_tickers":
            await callback.message.answer(
                "🔙 <b>Возврат к выбору тикера</b>\n\n"
                "<i>Выберите сферу для поиска тикера:</i>",
                reply_markup=quote_menu(),
                parse_mode="HTML"
            )
        
        elif back_data.startswith("back_to_assets_"):
            ticker = back_data.replace("back_to_assets_", "")
            
            company_info = await quote_service.get_company_info(ticker)
            
            if company_info:
                message_text = await quote_service.format_company_message(company_info)
                message_text += "\n\n👇 <b>Выберите тип актива:</b>"
            else:
                message_text = f"""
📊 <b>{ticker}</b>

👇 <b>Выберите тип актива для просмотра:</b>
"""
            
            await callback.message.answer(
                message_text,
                reply_markup=asset_type(ticker),
                parse_mode="HTML"
            )
        
        elif back_data.startswith("back_to_data_"):
            data = back_data.replace("back_to_data_", "")
            ticker, asset_type = data.split("_", 1)
            
            # Эмулируем выбор типа актива
            callback.data = f"asset_{asset_type}_{ticker}"
            await handle_asset_type_selection(callback)
            return
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_back_navigation: {e}")
        await callback.answer("Ошибка навигации")

@quote_router.callback_query(F.data.startswith("analysis_"))
async def show_technical(callback: CallbackQuery):
    try:
        data = callback.data.replace("analysis_", "")
        ticker, asset_type = data.split("_", 1)
        
        await callback.message.answer(
            f"📊 <b>Технический анализ: {ticker}</b>\n\n"
            "Выберите индикатор:\n\n"
            "<i>Технический анализ временно недоступен</i>\n"
            "<i>Функция в разработке</i>",
            reply_markup=technical_analysis_menu(ticker, asset_type),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_technical: {e}")
        await callback.answer("Ошибка загрузки анализа")

@quote_router.callback_query(F.data.startswith("ta_"))
async def show_technical_indicator(callback: CallbackQuery):
    try:
        data = callback.data.replace("ta_", "")
        indicator, ticker, asset_type = data.split("_", 2)
        
        loading_msg = await callback.message.answer(
            f"📊 <b>Генерация графика с {indicator.upper()}...</b>\n\n"
            f"<i>{ticker} - технический анализ</i>",
            parse_mode="HTML"
        )
        
        try:
            chart_image = await quote_service.generate_technical_chart(
                ticker, asset_type, indicator
            )
            
            if chart_image:
                image_file = BufferedInputFile(
                    chart_image,
                    filename=f"{ticker}_{indicator}.png"
                )
                
                await callback.message.answer_photo(
                    photo=image_file,
                    caption=f"📊 <b>{ticker} - {indicator.upper()}</b>\n"
                           f"💼 <i>Технический анализ</i>",
                    parse_mode="HTML"
                )
                await loading_msg.delete()
            else:
                await loading_msg.edit_text(
                    f"❌ <b>Не удалось сгенерировать график</b>\n\n"
                    f"<i>Технический анализ временно недоступен</i>\n"
                    f"<i>Функция в разработке</i>",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка технического анализа: {e}")
            await loading_msg.edit_text(
                f"❌ <b>Ошибка при генерации графика</b>\n\n"
                f"<i>Попробуйте позже</i>",
                parse_mode="HTML"
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_technical_indicator: {e}")
        await callback.answer("Ошибка технического анализа")

@quote_router.callback_query(F.data == "ignore")
async def handle_ignore(callback: CallbackQuery):
    await callback.answer()

@quote_router.callback_query(F.data == "refresh")
async def handle_refresh(callback: CallbackQuery):
    await callback.answer("🔄 Обновление...")
