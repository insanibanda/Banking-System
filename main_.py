import random
import string
import psycopg2
import os
from Database import connect_to_database
# ==================== DATABASE TABLE INITIALIZATION ====================
def initialize_tables():
    connection = connect_to_database()
    if not connection:
        return False
        
    try:
        cursor = connection.cursor()
        
        create_accounts_table = """
        CREATE TABLE IF NOT EXISTS accounts (
            account_number VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            pin VARCHAR(4) NOT NULL,
            balance DECIMAL(15, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_audit_table = """
        CREATE TABLE IF NOT EXISTS audit (
            id SERIAL PRIMARY KEY,
            account_number VARCHAR(50),
            holder_name VARCHAR(100),
            action VARCHAR(100) NOT NULL,
            amount DECIMAL(15, 2) DEFAULT 0.00,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_number) REFERENCES accounts(account_number)
        );
        """
        
        cursor.execute(create_accounts_table)
        cursor.execute(create_audit_table)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as error:
        print(f"Error initializing tables: {error}")
        if connection:
            connection.close()
        return False

# ==================== AUDIT CLASS ====================
class Audit:

    @staticmethod
    def log_action(account_number, holder_name, action, amount = 0.0):
        connection = connect_to_database()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO audit (account_number, holder_name, action, amount) VALUES (%s, %s, %s, %s)",
                (account_number, holder_name, action, amount)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as error:
            print(f"Error logging audit action: {error}")
            if connection:
                connection.close()
            return False
    
    @staticmethod
    def get_audit_logs(account_number):
        connection = connect_to_database()
        if not connection:
            return []
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, holder_name, action, amount, timestamp 
                FROM audit 
                WHERE account_number = %s 
                ORDER BY timestamp DESC
                """,
                (account_number,)
            )
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            
            logs = []
            for row in results:
                logs.append({
                    'id': row[0],
                    'holder_name': row[1],
                    'action': row[2],
                    'amount': float(row[3]),
                    'timestamp': row[4]
                })
            return logs
        except Exception as error:
            print(f"Error retrieving audit logs: {error}")
            if connection:
                connection.close()
            return []
    
    @staticmethod
    def get_all_audit_logs():
        connection = connect_to_database()
        if not connection:
            return []
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, account_number, holder_name, action, amount, timestamp 
                FROM audit 
                ORDER BY timestamp DESC
                """
            )
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            
            logs = []
            for row in results:
                logs.append({
                    'id': row[0],
                    'account_number': row[1],
                    'holder_name': row[2],
                    'action': row[3],
                    'amount': float(row[4]),
                    'timestamp': row[5]
                })
            return logs
        except Exception as error:
            print(f"Error retrieving all audit logs: {error}")
            if connection:
                connection.close()
            return []
    
    @staticmethod
    def clear_audit_logs():
        connection = connect_to_database()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM audit")
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as error:
            print(f"Error clearing audit logs: {error}")
            if connection:
                connection.close()
            return False




# ==================== ACCOUNT CLASS ====================
class Account:
    
    def __init__(self, name = "", pin = "", account_number = ""):
        # Private attributes taaki encapsulation ensure ho
        self.__account_number = account_number if account_number else self.__generate_account_number()
        self.__name = name
        self.__pin = pin
        self.__balance = 0.0
        
    @staticmethod
    def __generate_account_number():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # GETTER METHODS - Private attributes tak controlled access provide karta hai
    def get_account_number(self):
        return self.__account_number
    
    def get_name(self):
        return self.__name
    
    def get_balance(self):
        return self.__balance
    
    def get_pin(self):
        return self.__pin
    
    # SETTER METHODS - Private attributes mein controlled modification karta hai
    def set_name(self, name):
        self.__name = name
    
    def set_pin(self, pin):
        self.__pin = pin
    
    def set_balance(self, balance):
        self.__balance = balance
    
    def deposit(self, amount):
        if amount <= 0:
            return False
        self.__balance += amount
        return True
    
    def withdraw(self, amount):
        if amount <= 0 or amount > self.__balance:
            return False
        self.__balance -= amount
        return True
    
    @classmethod
    def load_from_db(cls, account_number, pin):
        connection = connect_to_database()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT account_number, name, pin, balance FROM accounts WHERE account_number = %s AND pin = %s",
                (account_number, pin)
            )
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result:
                # Account object database data ke saath banata hai
                account = cls(result[1], result[2], result[0])
                account.set_balance(float(result[3]))
                return account
            return None
        except Exception as error:
            print(f"Error loading account: {error}")
            if connection:
                connection.close()
            return None
    
    def save_to_db(self):
        connection = connect_to_database()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO accounts (account_number, name, pin, balance)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (account_number)
                DO UPDATE SET name = %s, pin = %s, balance = %s
                """,
                (self.__account_number, self.__name, self.__pin, self.__balance,
                 self.__name, self.__pin, self.__balance)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as error:
            print(f"Error saving account: {error}")
            if connection:
                connection.close()
            return False
    
    def delete_from_db(self):
        connection = connect_to_database()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM accounts WHERE account_number = %s", (self.__account_number,))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as error:
            print(f"Error deleting account: {error}")
            if connection:
                connection.close()
            return False

# ==================== BANK SYSTEM CLASS ====================
class BankSystem:
    
    def __init__(self):
        initialize_tables()
    
    def create_account(self, name, pin):
        account = Account(name, pin)
        if account.save_to_db():
            # Account creation ko audit trail mein log karta hai
            Audit.log_action(account.get_account_number(), account.get_name(), "Account Created", 0.0)
            return account
        return None
    
    def read_account(self, account_number, pin):
        account = Account.load_from_db(account_number, pin)
        if account:
            # Balance check ko audit trail mein log karta hai
            Audit.log_action(account_number, account.get_name(), "Balance checked", 0.0)
        return account
    
    def update_account(self, account):
        return account.save_to_db()
    
    def delete_account(self, account_number, pin):
        account = Account.load_from_db(account_number, pin)
        if account:
            success = account.delete_from_db()
            if success:
                # Account deletion ko audit trail mein log karta hai
                Audit.log_action(account_number, account.get_name(), "Account Deleted", 0.0)
                return True
        return False
    
    def deposit(self, account_number, pin, amount):
        account = Account.load_from_db(account_number, pin)
        if account and account.deposit(amount):
            if account.save_to_db():
                # Deposit ko audit trail mein log karta hai
                Audit.log_action(account_number, account.get_name(), "Amount deposited", amount)
                return True
        return False
    
    def withdraw(self, account_number, pin, amount):
        account = Account.load_from_db(account_number, pin)
        if account and account.withdraw(amount):
            if account.save_to_db():
                # Withdrawal ko audit trail mein log karta hai
                Audit.log_action(account_number, account.get_name(), "Amount withdrawn", amount)
                return True
        return False
    
    def get_account_balance(self, account_number, pin):
        account = self.read_account(account_number, pin)
        return account.get_balance() if account else None
    
    def get_audit_logs(self, account_number):
        return Audit.get_audit_logs(account_number)
    
    def get_all_audit_logs(self):
        return Audit.get_all_audit_logs()
    
    def clear_audit_logs(self):
        return Audit.clear_audit_logs()

# ==================== UTILITY FUNCTIONS ====================
def get_valid_amount(prompt):
    while True:
        try:
            amount = float(input(prompt))
            if amount <= 0:
                print("Amount must be greater than zero.")
                continue
            return amount
        except ValueError:
            print("Please enter a valid number.")

# ==================== CLI MENU FUNCTIONS ====================
def create_account_cli(bank):
    print("=" * 40)
    print("        CREATE NEW ACCOUNT")
    print("=" * 40)
    
    name = input("Enter your name: ").strip()
    if not name:
        print("Aree Naam khali nahi ho sakta.")
        input("Press Enter to continue...")
        return
    
    # PIN le leta hai bina masking ke
    pin = input("4-digit PIN daalo: ").strip()
    if len(pin) != 4 or not pin.isdigit():
        print("PIN ek 4-digit number hona chahiye.")
        input("Press Enter to continue...")
        return
    
    confirm_pin = input("Apna PIN confirm karo: ").strip()
    if pin != confirm_pin:
        print("PINs match nahi ho rahe.")
        input("Press Enter to continue...")
        return
    
    account = bank.create_account(name, pin)
    if account:
        print(f"\nAccount successfully ban gaya!")
        print(f"Account Number: {account.get_account_number()}")
        print("Apna account number aur PIN securely save karo.")
    else:
        print("\nAccount banana fail ho gaya. Kripya fir se try karein.")
    
    input("Press Enter to continue...")

def login_to_account_cli(bank):
    print("=" * 40)
    print("          ACCOUNT LOGIN")
    print("=" * 40)
    
    account_number = input("Apna account number daalo: ").strip()
    if not account_number:
        print("Account number khali nahi ho sakta.")
        input("Press Enter to continue...")
        return
    
    pin = input("Apna PIN daalo: ").strip()
    
    account = bank.read_account(account_number, pin)
    if not account:
        print("Galat account number ya PIN.")
        input("Press Enter to continue...")
        return
    
    # Account operations menu
    while True:
        print("=" * 40)
        print(f"        WELCOME, {account.get_name()}!")
        print(f"        ACCOUNT: {account.get_account_number()}")
        print("=" * 40)
        print("1. Balance Check karo")
        print("2. Paise jama karo")
        print("3. Paise nikalo")
        print("4. Transaction History dekho")
        print("5. Account Info update karo")
        print("6. Account delete karo")
        print("7. Logout")
        print("=" * 40)
        
        choice = input("Apna choice daalo (1-7): ").strip()
        
        if choice == '1':
            check_balance_cli(bank, account)
        elif choice == '2':
            deposit_money_cli(bank, account)
        elif choice == '3':
            withdraw_money_cli(bank, account)
        elif choice == '4':
            view_transaction_history_cli(bank, account)
        elif choice == '5':
            update_account_info_cli(bank, account)
        elif choice == '6':
            if delete_account_cli(bank, account):
                break  # Deletion ke baad main menu par wapas jaao
        elif choice == '7':
            break  # Logout
        else:
            print("Galat choice. Kripya fir se try karein.")
            input("Press Enter to continue...")

def check_balance_cli(bank, account):
    print("=" * 40)
    print("         ACCOUNT BALANCE")
    print("=" * 40)
    
    balance = bank.get_account_balance(account.get_account_number(), account.get_pin())
    if balance is not None:
        print(f"Current Balance: ${balance:.2f}")
    else:
        print("Balance nikalne mein error aaya.")
    
    input("Press Enter to continue...")

def deposit_money_cli(bank, account):
    print("=" * 40)
    print("          Paise Jama Karo")
    print("=" * 40)
    
    amount = get_valid_amount("Jitne paise jama karne hain wo daalo: $")
    
    if bank.deposit(account.get_account_number(), account.get_pin(), amount):
        print(f"${amount:.2f} successfully jama ho gaye!")
        # Display ke liye account balance update karo
        account = bank.read_account(account.get_account_number(), account.get_pin())
        if account:
            print(f"Naya Balance: ${account.get_balance():.2f}")
    else:
        print("Paise jama karne mein problem aayi. Kripya fir se try karein.")
    
    input("Press Enter to continue...")

def withdraw_money_cli(bank, account):
    print("=" * 40)
    print("         Paise Nikalo")
    print("=" * 40)
    
    amount = get_valid_amount("Kitne paise nikalne hain wo daalo: $")
    
    if bank.withdraw(account.get_account_number(), account.get_pin(), amount):
        print(f"${amount:.2f} successfully nikal diye gaye!")
        # Display ke liye account balance update karo
        account = bank.read_account(account.get_account_number(), account.get_pin())
        if account:
            print(f"Naya Balance: ${account.get_balance():.2f}")
    else:
        print("Paise nikalne mein problem aayi. Kam paise hain ya galat amount.")
    
    input("Press Enter to continue...")

def view_transaction_history_cli(bank, account):
    print("=" * 40)
    print("      TRANSACTION HISTORY")
    print("=" * 40)
    
    logs = bank.get_audit_logs(account.get_account_number())
    if not logs:
        print("Koi transaction history nahi mili.")
    else:
        print(f"{'ID':<5} {'Naam':<15} {'Action':<20} {'Amount':<10} {'Time':<20}")
        print("-" * 70)
        for log in logs:
            amount_str = f"${log['amount']:.2f}" if log['amount'] > 0 else ""
            print(f"{log['id']:<5} {log['holder_name']:<15} {log['action']:<20} {amount_str:<10} {log['timestamp']:<20}")
    
    input("Press Enter to continue...")

def update_account_info_cli(bank, account):
    print("=" * 40)
    print("      ACCOUNT INFO UPDATE KARO")
    print("=" * 40)
    print("1. Naam badlo")
    print("2. PIN badlo")
    print("3. Account Menu par wapas jao")
    print("=" * 40)
    
    choice = input("Apna choice daalo (1-3): ").strip()
    
    if choice == '1':
        new_name = input("Naya naam daalo: ").strip()
        if new_name:
            account.set_name(new_name)
            if bank.update_account(account):
                print("Naam successfully update ho gaya!")
            else:
                print("Naam update karne mein problem aayi.")
        else:
            print("Naam khali nahi ho sakta.")
    elif choice == '2':
        old_pin = input("Current PIN daalo: ").strip()
        if old_pin == account.get_pin():
            new_pin = input("Naya 4-digit PIN daalo: ").strip()
            if len(new_pin) == 4 and new_pin.isdigit():
                confirm_pin = input("Naya PIN confirm karo: ").strip()
                if new_pin == confirm_pin:
                    account.set_pin(new_pin)
                    if bank.update_account(account):
                        print("PIN successfully update ho gaya!")
                    else:
                        print("PIN update karne mein problem aayi.")
                else:
                    print("PINs match nahi ho rahe.")
            else:
                print("PIN ek 4-digit number hona chahiye.")
        else:
            print("Galat current PIN.")
    elif choice != '3':
        print("Galat choice.")
    
    input("Press Enter to continue...")

def delete_account_cli(bank, account):
    print("=" * 40)
    print("        ACCOUNT DELETE KARO")
    print("=" * 40)
    print("WARNING: Ye action wapas nahi kiya ja sakta!")
    print("Confirmation ke liye aapko dena hoga:")
    print(f"1. Account Number: {account.get_account_number()}")
    print("2. Apka PIN")
    print("=" * 40)
    
    confirmation = input("Kya aap sach mein apna account delete karna chahte hain? (yes/no): ").strip().lower()
    if confirmation != 'yes':
        print("Account deletion cancel ho gaya.")
        input("Press Enter to continue...")
        return False
    
    # Security ke liye account number aur PIN verify karo
    acc_num_input = input("Apna account number fir se daalo: ").strip()
    pin_input = input("Apna PIN daalo: ").strip()
    
    if acc_num_input == account.get_account_number() and pin_input == account.get_pin():
        if bank.delete_account(account.get_account_number(), account.get_pin()):
            print("Account successfully delete ho gaya!")
            input("Press Enter to continue...")
            return True
        else:
            print("Account delete karne mein problem aayi.")
    else:
        print("Account number ya PIN galat hai. Deletion cancel ho gaya.")
    
    input("Press Enter to continue...")
    return False

def admin_view_audit_logs_cli(bank):
    print("=" * 40)
    print("       SAB AUDIT LOGS")
    print("=" * 40)
    
    # Security ke liye real system mein iski protection password se ki ja sakti hai
    logs = bank.get_all_audit_logs()
    if not logs:
        print("Koi audit logs nahi mili.")
    else:
        print(f"{'ID':<5} {'Account':<12} {'Naam':<15} {'Action':<20} {'Amount':<10} {'Time':<20}")
        print("-" * 85)
        for log in logs:
            amount_str = f"${log['amount']:.2f}" if log['amount'] > 0 else ""
            print(f"{log['id']:<5} {log['account_number']:<12} {log['holder_name']:<15} {log['action']:<20} {amount_str:<10} {log['timestamp']:<20}")
    
    input("Press Enter to continue...")

def admin_clear_audit_logs_cli(bank):
    print("=" * 40)
    print("      AUDIT LOGS CLEAR KARO")
    print("=" * 40)
    print("WARNING: Ye sab audit logs ko permanent delete kar dega!")
    print("=" * 40)
    
    confirmation = input("Kya aap sach mein sab audit logs clear karna chahte hain? (yes/no): ").strip().lower()
    if confirmation == 'yes':
        if bank.clear_audit_logs():
            print("Sab audit logs successfully clear ho gayi!")
        else:
            print("Audit logs clear karne mein problem aayi.")
    else:
        print("Operation cancel ho gaya.")
    
    input("Press Enter to continue...")

def main_menu_cli():
    bank = BankSystem()
    
    while True:
        print("=" * 40)
        print("        BANK MANAGEMENT SYSTEM")
        print("=" * 40)
        print("1. Naya Account Banayein")
        print("2. Account Par Login Karein")
        print("3. Admin - Sab Audit Logs Dekhein")
        print("4. Admin - Audit Logs Clear Karein")
        print("5. Exit")
        print("=" * 40)
        
        choice = input("Apna choice daalo (1-5): ").strip()
        
        if choice == '1':
            create_account_cli(bank)
        elif choice == '2':
            login_to_account_cli(bank)
        elif choice == '3':
            admin_view_audit_logs_cli(bank)
        elif choice == '4':
            admin_clear_audit_logs_cli(bank)
        elif choice == '5':
            print("Hamare Bank Management System ka istemal karne ke liye dhanyavaad!")
            break
        else:
            print("Galat choice. Kripya fir se try karein.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main_menu_cli()