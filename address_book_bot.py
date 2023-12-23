import sys
import pickle
from collections import UserDict
from datetime import datetime


class Field:
    """Базовий клас для полів запису"""
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __str__(self):
        return str(self.value)

class Name(Field):
    """Клас для зберігання імені контакту"""
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty")
        super().__init__(value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value


class Phone(Field):
    """Клас для зберігання номера телефону"""
    def __init__(self, value):
        self.validate_phone_format(value)
        super().__init__(value)

    def validate_phone_format(self, value):
        """Метод проводить валідацію номера - 10 цифр"""
        if value and not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number should be a 10-digit number")

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value


class Birthday(Field):
    """Клас для зберігання дня народження"""
    def __init__(self, value=None):
        self.validate_birthday_format(value)
        super().__init__(value)

    def validate_birthday_format(self, value):
        """Метод проводить валідацію дати"""
        try:
            return datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Birthday is not a date")

class Record:
    """Клас для зберігання інформації про контакт, включаючи ім'я та список телефонів"""
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone_number):
        """Метод для додавання об'єктів"""
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        """Метод для видалення об'єктів"""
        for phone in self.phones:
            if phone.value == phone_number:
                self.phones.remove(phone)
                break

    def find_phone(self, phone_number):
        """Метод для пошуку об'єктів"""
        for phone in self.phones:
            if phone == Phone(phone_number):
                return phone
        return None

    def edit_phone(self, old_phone_number, new_phone_number):
        """Метод для редагування об'єктів"""
        for phone in self.phones:
            if phone.value == old_phone_number:
                phone.value = new_phone_number
                return

        raise ValueError("Phone number to be edited was not found")

    def days_to_birthday(self):
        """Метод для обчислення кількості днів до наступного дня народження"""
        if isinstance(self.birthday, Birthday):
            today = datetime.now()
            today_birthday = datetime(today.year, today.month, today.day)
            day = int(self.birthday.value.strftime("%d"))
            month = int(self.birthday.value.strftime("%m"))
            year = int(today.year)
            next_birthday = datetime(year, month, day)
            if next_birthday < today_birthday:
                year = int(today.year + 1)
                next_birthday = datetime(year, month, day)
            days_left = (next_birthday - today_birthday).days
            return days_left
        return NotImplemented

    def __str__(self):
        """Метод створює рядок"""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    """Клас для зберігання та управління записами"""
    def add_record(self, record):
        """Метод додає запис до self.data"""
        record_name = record.name.value
        self.data[record_name] = record

    def find(self, name):
        """Метод знаходить запис за ім'ям"""
        if name in self.data:
            return self.data[name]
        return None

    def delete(self, name):
        """Метод видаляє запис за ім'ям"""
        if name in self.data:
            del self.data[name]

    def iterate(self, records_per_iteration=5):
        """Метод повертає генератор за записами і за одну ітерацію повертає декілька записів"""
        keys = list(self.data.keys())
        records = 0
        all_records = len(keys)
        while records < all_records:
            yield [self.data[keys[i]] for i in range(records, min(records + records_per_iteration, all_records))]
            records += records_per_iteration

    def write_to_file(self, filename):
        """Метод зберігає адресну книгу у файл"""
        with open(filename, "wb") as fh:
            pickle.dump(self.data, fh)        


    @classmethod
    def read_contacts_from_file(cls, filename):
        """Метод відновлює адресну книгу з файлу"""
        try:
            with open(filename, 'rb') as fh:
                data = pickle.load(fh)
                address_book = cls()
                address_book.data = data
                return address_book
        except (FileNotFoundError, EOFError)  as err:
            return AddressBook()


    def __getstate__(self):
        """Метод контролю серіалізації"""
        state = self.__dict__.copy()
        return state


    def __setstate__(self, state):
        """Метод контролю десеріалізації"""
        self.__dict__.update(state)


    def search(self, query):
        """Метод проводить пошук записів за частковим збігом імені або номера телефону"""
        found_records = []
        for record in self.data.values():
            if query in record.name.value or any(query in phone.value for phone in record.phones):
                found_records.append(record)
        return found_records


def errors_commands(func):
    """Функія-декоратор, що ловить помилки вводу"""
    def inner(*args):
        try:
            return func(*args)
        except (KeyError, ValueError, IndexError, TypeError) as err:
            error_messages = {
                KeyError: "Contact not found.",
                ValueError: "Give me name and phone please.",
                IndexError: "Index out of range. Please provide valid input",
                TypeError: "Invalid number of arguments."
            }
            return error_messages.get(type(err), "An error occurred.")
    return inner


def hello_user():
    """Функція обробляє команду-привітання 'hello'
    """
    return "How can I help you?"

    
@errors_commands
def add_contact(name, phone):
    """Функція обробляє команду 'add'"""
    global _address_book
    try:
        if not name.isalpha() or not phone.isnumeric():
            raise ValueError
        record = Record(name)
        record.add_phone(phone)
        _address_book.add_record(record)
        return f"Contact {name} added."
    except Exception as err:
        return str(err)


@errors_commands
def change_phone(name, phone):
    """Функція обробляє команду 'change'"""
    global _address_book
    try:
        record = _address_book.find(name)
        if not record:
            raise KeyError("Contact not found.")
        if not phone.isnumeric():
            raise ValueError("Invalid phone number.")
        record.edit_phone(record.phones[0].value, phone)  # assuming only one phone per contact
        _address_book.write_to_file("my_address_book")
        return f"Phone {name} changed."
    except Exception as err:
        return str(err)


@errors_commands
def show_phone(name):
    """Функція обробляє команду 'phone'"""
    global _address_book
    try:
        record = _address_book.find(name)
        if not record:
            raise KeyError("Contact not found.")
        return f"The phone {name} is {record.phones[0].value}"  # assuming only one phone per contact
    except Exception as err:
        return str(err)


@errors_commands
def show_all():
    """Функція обробляє команду 'show all'"""
    global _address_book
    try:
        if _address_book:
            return "\n".join([f"{name}: {record.phones[0].value}" for name, record in _address_book.items()])
        return "No contacts found."
    except Exception as err:
        return str(err)

def farewell():
    """Функція обробляє команди виходу
    """
    return "Good bye!"


def parser_command(user_command):
    """Функція, яка обробляє команди користувача і повертає відповідь 
    """
    users_commands = {
        'hello': hello_user,
        'add': add_contact,
        'change': change_phone,
        'phone': show_phone,
        'show all': show_all,
        'good bye': farewell,
        'close': farewell,
        'exit': farewell
    }

    command = user_command[0]
    if command in users_commands:
        if len(user_command) > 1:
            parser_result = users_commands[command](*user_command[1:])
        else:
            parser_result = users_commands[command]()
    elif len(user_command) == 2:
        command_2 = user_command[0]+' '+ user_command[1]
        if command_2 in users_commands:
            parser_result = users_commands[command_2]()
    else:
        parser_result = 'Invalid command.'
    return parser_result

_address_book = None

def main():
    """Функція для обробки команд користувача через консоль"""
    global _address_book
    _address_book = AddressBook.read_contacts_from_file("my_address_book") # Зчитуємо дані з файлу при запуску

    while True:
        user_command = input("Please enter a command: ").lower().split()
        if not user_command:
            continue

        result = parser_command(user_command)
        print(result)

        if result == "Good bye!":
            _address_book.write_to_file("my_address_book")  # Записуємо дані у файл перед виходом
            sys.exit()

if __name__ == '__main__':
    main()
