from toga import App, Box, Button, MainWindow, Label, NumberInput, TextInput, Selection
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import random
import asyncio
import os

class SpyGame(App):
    def startup(self):
        # Основні змінні гри
        self.locations = [
            "Пляж", "Банк", "Школа", "Лікарня", "Військова база", "Казино",
            "Готель", "Ресторан", "Спа-салон", "Університет", "Літак",
            "Кінотеатр", "Цирк", "Круїзний корабель", "Посольство",
            "Супермаркет", "Музей", "Станція метро", "Полярна станція",
            "Театр", "Винний льох", "Зоопарк", "Похорон", "Весілля"
        ]
        
        self.players = []
        self.spies = []
        self.current_location = ""
        self.game_in_progress = False
        self.time_left = 360  # 6 хвилин
        self.viewed_roles = set()  # Гравці, які переглянули свої ролі
        
        # Створення основного вікна
        self.main_window = MainWindow(title="Шпигун")
        
        # Створення компонентів інтерфейсу
        self.setup_ui()
        
        # Показати вікно
        self.main_window.show()
    
    def setup_ui(self):
        # Головний контейнер
        main_box = Box(style=Pack(direction=COLUMN, padding=20))
        
        # Заголовок
        header_label = Label("Гра 'Шпигун'", style=Pack(font_weight='bold', font_size=20, padding_bottom=10))
        main_box.add(header_label)
        
        # Секція налаштувань гри
        setup_box = Box(style=Pack(direction=COLUMN, padding=10))
        main_box.add(setup_box)
        
        # Кількість гравців
        players_box = Box(style=Pack(direction=ROW, padding=5))
        players_label = Label("Кількість гравців:", style=Pack(padding_right=10))
        players_box.add(players_label)
        
        self.players_input = NumberInput(min_value=3, max_value=15, value=4, style=Pack(width=70))
        players_box.add(self.players_input)
        setup_box.add(players_box)
        
        # Кількість шпигунів
        spies_box = Box(style=Pack(direction=ROW, padding=5))
        spies_label = Label("Кількість шпигунів:", style=Pack(padding_right=10))
        spies_box.add(spies_label)
        
        self.spies_input = NumberInput(min_value=1, max_value=5, value=1, style=Pack(width=70))
        spies_box.add(self.spies_input)
        setup_box.add(spies_box)
        
        # Кнопка для додавання імен гравців
        self.add_players_button = Button("Додати імена гравців", on_press=self.add_player_names)
        setup_box.add(self.add_players_button)
        
        # Розділювач
        divider = Box(style=Pack(height=1, background_color="#CCCCCC", padding=10))
        main_box.add(divider)
        
        # Список гравців
        self.players_label = Label("Гравці:", style=Pack(font_weight='bold', padding_top=10))
        main_box.add(self.players_label)
        
        self.players_box = Box(style=Pack(direction=COLUMN, padding=5))
        main_box.add(self.players_box)
        
        # Кнопки керування грою
        control_box = Box(style=Pack(direction=ROW, padding=10))
        
        self.start_button = Button("Почати гру", on_press=self.start_game, enabled=False)
        control_box.add(self.start_button)
        
        self.end_button = Button("Завершити гру", on_press=self.end_game, enabled=False)
        control_box.add(self.end_button)
        
        main_box.add(control_box)
        
        # Таймер
        self.timer_label = Label("Час: 06:00", style=Pack(font_size=24, padding=10))
        main_box.add(self.timer_label)
        
        # Встановлення головного контейнера
        self.main_window.content = main_box
    
    async def add_player_names(self, widget):
        try:
            num_players = self.players_input.value
            if num_players < 3:
                self.main_window.info_dialog("Помилка", "Мінімальна кількість гравців: 3")
                return
                
            # Очистити попередній список гравців
            self.players = []
            
            # Видалити попередні мітки гравців
            for child in self.players_box.children:
                self.players_box.remove(child)
            
            # Відкрити діалоги для введення імен гравців
            for i in range(num_players):
                # У BeeWare немає прямого еквіваленту simpledialog.askstring
                # Тому створюємо своє модальне вікно
                player_name = await self.get_player_name_dialog(i)
                if not player_name:  # Якщо користувач не ввів ім'я
                    player_name = f"Гравець {i+1}"
                
                self.players.append(player_name)
                
                # Створити мітку для гравця
                player_label = Label(f"{i+1}. {player_name}", style=Pack(padding=5))
                self.players_box.add(player_label)
            
            self.main_window.info_dialog("Готово", f"Додано {num_players} гравців!")
            self.start_button.enabled = True
            
        except Exception as e:
            self.main_window.info_dialog("Помилка", f"Помилка при додаванні гравців: {e}")
    
    async def get_player_name_dialog(self, player_index):
        # Створюємо нове вікно для введення імені
        dialog_id = f"player_{player_index}_dialog"
        
        dialog = await self.stack_window(Dialog(self, f"Ім'я гравця {player_index+1}", dialog_id), self.main_window)
        result = await dialog.future
        return result
    
    async def start_game(self, widget):
        if not self.players:
            self.main_window.info_dialog("Помилка", "Спочатку додайте імена гравців")
            return
        
        try:
            num_spies = self.spies_input.value
            if num_spies < 1 or num_spies >= len(self.players):
                self.main_window.info_dialog("Помилка", f"Кількість шпигунів має бути від 1 до {len(self.players)-1}")
                return
                
            # Вибір локації
            self.current_location = random.choice(self.locations)
            
            # Вибір шпигунів
            self.spies = random.sample(range(len(self.players)), num_spies)
            
            # Оновлення стану гри
            self.game_in_progress = True
            self.start_button.enabled = False
            self.end_button.enabled = True
            
            # Скидаємо перелік гравців, які переглянули ролі
            self.viewed_roles = set()
            
            # Запуск таймера
            self.time_left = 360  # 6 хвилин
            
            # Створюємо асинхронну задачу для таймера
            asyncio.create_task(self.run_timer())
            
            # Відображення вікна для перегляду ролей
            await self.show_view_roles_dialog()
            
        except Exception as e:
            self.main_window.info_dialog("Помилка", f"Помилка при запуску гри: {e}")
    
    async def run_timer(self):
        while self.game_in_progress and self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            time_string = f"Час: {mins:02d}:{secs:02d}"
            self.timer_label.text = time_string
            await asyncio.sleep(1)
            self.time_left -= 1
        
        if self.time_left <= 0 and self.game_in_progress:
            # Таймер завершено
            await self.end_game(None)
    
    async def show_view_roles_dialog(self):
        # У BeeWare потрібно використовувати інший підхід для модальних вікон
        dialog = await self.stack_window(ViewRolesDialog(self), self.main_window)
        await dialog.future
    
    async def show_role(self, player_index):
        # Додаємо гравця до списку тих, хто переглянув роль
        self.viewed_roles.add(player_index)
        
        player_name = self.players[player_index]
        
        if player_index in self.spies:
            role_text = "Ви ШПИГУН!"
            location_text = "Ваше завдання - вгадати поточну локацію, уникаючи викриття."
        else:
            role_text = "Ви знаходитесь в локації:"
            location_text = self.current_location
        
        # Відображаємо роль
        dialog = await self.stack_window(RoleDialog(self, player_name, role_text, location_text), self.main_window)
        await dialog.future
        
        # Перевіряємо, чи всі гравці переглянули свої ролі
        if len(self.viewed_roles) < len(self.players):
            # Якщо не всі - показуємо вікно вибору гравця знову
            await self.show_view_roles_dialog()
        else:
            # Якщо всі гравці переглянули свої ролі - починаємо гру
            self.main_window.info_dialog("Гра почалася", "Всі гравці переглянули свої ролі. Гра почалася!")
    
    async def end_game(self, widget):
        if not self.game_in_progress:
            return
            
        # Оновлення стану гри
        self.game_in_progress = False
        self.start_button.enabled = True
        self.end_button.enabled = False
        
        # Відображення результатів
        await self.show_results()
    
    async def show_results(self):
        # Відображаємо результати гри
        dialog = await self.stack_window(ResultsDialog(self), self.main_window)
        await dialog.future


class Dialog:
    def __init__(self, app, title, dialog_id=None):
        self.app = app
        self.title = title
        self.id = dialog_id
        self.future = asyncio.Future()
    
    def create_dialog(self):
        # Створення вікна діалогу
        self.window = MainWindow(title=self.title)
        
        main_box = Box(style=Pack(direction=COLUMN, padding=20))
        self.window.content = main_box
        
        return main_box
    
    def close_dialog(self, result=None):
        self.window.close()
        self.future.set_result(result)


class PlayerNameDialog(Dialog):
    def __init__(self, app, player_index):
        super().__init__(app, f"Ім'я гравця {player_index+1}")
        self.player_index = player_index
        
        main_box = self.create_dialog()
        
        label = Label(f"Введіть ім'я гравця {player_index+1}:")
        main_box.add(label)
        
        self.name_input = TextInput(style=Pack(padding=10))
        main_box.add(self.name_input)
        
        button_box = Box(style=Pack(direction=ROW, padding=10))
        ok_button = Button("OK", on_press=self.on_ok_pressed)
        button_box.add(ok_button)
        
        main_box.add(button_box)
    
    def on_ok_pressed(self, widget):
        self.close_dialog(self.name_input.value)


class ViewRolesDialog(Dialog):
    def __init__(self, app):
        super().__init__(app, "Перегляд ролей")
        
        main_box = self.create_dialog()
        
        label = Label("Виберіть гравця для перегляду ролі:", style=Pack(font_size=16, padding=10))
        main_box.add(label)
        
        players_box = Box(style=Pack(direction=COLUMN, padding=10))
        
        for i, player in enumerate(app.players):
            if i not in app.viewed_roles:  # Перевіряємо, чи не переглянув вже гравець свою роль
                button = Button(
                    player,
                    on_press=self.on_player_selected,
                    style=Pack(padding=8),
                    id=str(i)  # Зберігаємо індекс як id
                )
                players_box.add(button)
        
        main_box.add(players_box)
    
    async def on_player_selected(self, widget):
        player_index = int(widget.id)
        self.close_dialog()
        await self.app.show_role(player_index)


class RoleDialog(Dialog):
    def __init__(self, app, player_name, role_text, location_text):
        super().__init__(app, "Ваша роль")
        
        main_box = self.create_dialog()
        
        # Гравець
        player_label = Label(f"Гравець: {player_name}", style=Pack(font_size=18, font_weight='bold', padding=10))
        main_box.add(player_label)
        
        # Роль
        role_label = Label(role_text, style=Pack(font_size=16, padding=10))
        main_box.add(role_label)
        
        # Локація
        location_label = Label(location_text, style=Pack(font_size=20, font_weight='bold', padding=20))
        main_box.add(location_label)
        
        # Кнопка "Зрозуміло"
        ok_button = Button("Зрозуміло", on_press=self.on_ok_pressed, style=Pack(padding=10))
        main_box.add(ok_button)
    
    def on_ok_pressed(self, widget):
        self.close_dialog()


class ResultsDialog(Dialog):
    def __init__(self, app):
        super().__init__(app, "Результати гри")
        
        main_box = self.create_dialog()
        
        # Заголовок
        header_label = Label("Результати гри", style=Pack(font_size=20, font_weight='bold', padding=10))
        main_box.add(header_label)
        
        # Локація
        location_box = Box(style=Pack(direction=COLUMN, padding=10))
        location_label = Label("Локація:", style=Pack(font_size=16, padding=5))
        location_box.add(location_label)
        
        current_location_label = Label(app.current_location, style=Pack(font_size=18, font_weight='bold', padding=5))
        location_box.add(current_location_label)
        
        main_box.add(location_box)
        
        # Шпигуни
        spies_box = Box(style=Pack(direction=COLUMN, padding=10))
        spies_label = Label("Шпигуни:", style=Pack(font_size=16, padding=5))
        spies_box.add(spies_label)
        
        for spy_index in app.spies:
            spy_name = app.players[spy_index]
            spy_item_label = Label(f"• {spy_name}", style=Pack(font_size=16, padding=2))
            spies_box.add(spy_item_label)
        
        main_box.add(spies_box)
        
        # Звичайні гравці
        players_box = Box(style=Pack(direction=COLUMN, padding=10))
        players_label = Label("Звичайні гравці:", style=Pack(font_size=16, padding=5))
        players_box.add(players_label)
        
        for i, player in enumerate(app.players):
            if i not in app.spies:
                player_item_label = Label(f"• {player}", style=Pack(font_size=16, padding=2))
                players_box.add(player_item_label)
        
        main_box.add(players_box)
        
        # Кнопка "OK"
        ok_button = Button("Нова гра", on_press=self.on_ok_pressed, style=Pack(padding=10))
        main_box.add(ok_button)
    
    def on_ok_pressed(self, widget):
        self.close_dialog()


def main():
    return SpyGame('ua.spygame', 'Шпигун')


if __name__ == '__main__':
    app = main()
    app.main_loop()
