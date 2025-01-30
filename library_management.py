import sqlite3
from datetime import datetime, timedelta

# Connect to SQLite database
conn = sqlite3.connect('library_management.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT NOT NULL,
    available INTEGER DEFAULT 1
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    borrow_date TEXT NOT NULL,
    return_date TEXT,
    fine INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (book_id) REFERENCES books (book_id)
)
''')
conn.commit()

# Helper function to calculate fine
def calculate_fine(borrow_date):
    return_date = datetime.now()
    borrow_date = datetime.strptime(borrow_date, '%Y-%m-%d')
    days_overdue = (return_date - borrow_date).days - 14
    return max(0, days_overdue) * 5  # $5 per day fine

# User authentication
def authenticate_user():
    username = input("Enter username: ")
    password = input("Enter password: ")
    cursor.execute('SELECT user_id, role FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    if user:
        return user  # Returns (user_id, role)
    else:
        print("Invalid username or password!")
        return None

# Admin functions
def add_book():
    title = input("Enter book title: ")
    author = input("Enter book author: ")
    genre = input("Enter book genre: ")
    cursor.execute('INSERT INTO books (title, author, genre) VALUES (?, ?, ?)', (title, author, genre))
    conn.commit()
    print("Book added successfully!")

def update_book():
    book_id = int(input("Enter book ID to update: "))
    title = input("Enter new title: ")
    author = input("Enter new author: ")
    genre = input("Enter new genre: ")
    cursor.execute('UPDATE books SET title = ?, author = ?, genre = ? WHERE book_id = ?', (title, author, genre, book_id))
    conn.commit()
    print("Book updated successfully!")

def delete_book():
    book_id = int(input("Enter book ID to delete: "))
    cursor.execute('DELETE FROM books WHERE book_id = ?', (book_id,))
    conn.commit()
    print("Book deleted successfully!")

def view_books():
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()
    if not books:
        print("No books found!")
    else:
        print("\nBooks:")
        for book in books:
            print(f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, Genre: {book[3]}, Available: {'Yes' if book[4] else 'No'}")

# User functions
def borrow_book(user_id):
    book_id = int(input("Enter book ID to borrow: "))
    cursor.execute('SELECT available FROM books WHERE book_id = ?', (book_id,))
    book = cursor.fetchone()
    if book and book[0]:
        borrow_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('INSERT INTO transactions (user_id, book_id, borrow_date) VALUES (?, ?, ?)', (user_id, book_id, borrow_date))
        cursor.execute('UPDATE books SET available = 0 WHERE book_id = ?', (book_id,))
        conn.commit()
        print("Book borrowed successfully!")
    else:
        print("Book not available!")

def return_book(user_id):
    book_id = int(input("Enter book ID to return: "))
    cursor.execute('SELECT borrow_date FROM transactions WHERE user_id = ? AND book_id = ? AND return_date IS NULL', (user_id, book_id))
    transaction = cursor.fetchone()
    if transaction:
        fine = calculate_fine(transaction[0])
        return_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('UPDATE transactions SET return_date = ?, fine = ? WHERE user_id = ? AND book_id = ?', (return_date, fine, user_id, book_id))
        cursor.execute('UPDATE books SET available = 1 WHERE book_id = ?', (book_id,))
        conn.commit()
        print(f"Book returned successfully! Fine: ${fine}")
    else:
        print("No such borrowing record found!")

def view_borrowing_history(user_id):
    cursor.execute('''
    SELECT books.title, transactions.borrow_date, transactions.return_date, transactions.fine
    FROM transactions
    JOIN books ON transactions.book_id = books.book_id
    WHERE transactions.user_id = ?
    ''', (user_id,))
    history = cursor.fetchall()
    if not history:
        print("No borrowing history found!")
    else:
        print("\nBorrowing History:")
        for record in history:
            print(f"Title: {record[0]}, Borrowed: {record[1]}, Returned: {record[2]}, Fine: ${record[3]}")

# Main menu
def main():
    user = authenticate_user()
    if not user:
        return

    user_id, role = user
    if role == 'admin':
        while True:
            print("\nAdmin Menu")
            print("1. Add Book")
            print("2. Update Book")
            print("3. Delete Book")
            print("4. View Books")
            print("5. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                add_book()
            elif choice == '2':
                update_book()
            elif choice == '3':
                delete_book()
            elif choice == '4':
                view_books()
            elif choice == '5':
                print("Exiting admin menu.")
                break
            else:
                print("Invalid choice!")
    else:
        while True:
            print("\nUser Menu")
            print("1. Borrow Book")
            print("2. Return Book")
            print("3. View Borrowing History")
            print("4. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                borrow_book(user_id)
            elif choice == '2':
                return_book(user_id)
            elif choice == '3':
                view_borrowing_history(user_id)
            elif choice == '4':
                print("Exiting user menu.")
                break
            else:
                print("Invalid choice!")

if __name__ == "__main__":
    cursor.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', 'admin123', 'admin'))
    conn.commit()
    main()
    conn.close()
