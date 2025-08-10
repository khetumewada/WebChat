# WebChat
A simple web chat application built with Django, Django Channels, and PostgreSQL. This project allows users to chat in real-time and supports user authentication.
## Features
- Real-time messaging using WebSockets
- User authentication (registration, login, logout)
- Message persistence with PostgreSQL
- Responsive design for various devices
- Static and media file handling
- User-friendly interface
## Technologies Used
- **Django**: A high-level Python web framework for rapid development.
- **Django Channels**: Extends Django to handle WebSockets and asynchronous protocols.
- **PostgreSQL**: A powerful, open-source relational database.
- **Redis**: An in-memory data structure store, used as a message broker for Django Channels.
- **Whitenoise**: For serving static files in production.
- **HTML/CSS/JavaScript**: Frontend technologies for building the user interface.
## Requirements
- Python 3.8 or higher
- PostgreSQL
- Redis (for channel layers)
- pip (Python package installer)
## Installation
Follow these steps to set up the project locally:
1. **Clone the repository:**
   - git clone: https://github.com/yourusername/WebChat.git
2. **Create a virtual environment:**
   - python -m venv venv
3. **Activate the virtual environment:**
   - On Windows:  venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate
4. **Install the required packages:**
   -   pip install -r requirements.txt
5. **Set up the database:**
   - Create a PostgreSQL database and user.
   - Update the database settings in `settings.py` to match your PostgreSQL configuration.
6. **Run database migrations:**
   -  python manage.py migrate
7. **Create a `.env` file for environment variables:**
   Create a file named `.env` in the root directory of the project and add the following content:
   - SECRET_KEY='your_secret_key'
   - DEBUG=True
   - DB_NAME='your_db_name'
   - DB_USER='your_db_user'
   - DB_PASSWORD='your_db_password'
   - DB_HOST='localhost'
   - DB_PORT='5432'
8. **Run the development server:**
   - python manage.py runserver
9. **Access the application:**
   - Open your web browser and go to `http://127.0.0.1:8000`.

## Usage
- Register a new account or log in with an existing account.
- Join a chat room and start messaging in real-time.
- Enjoy a responsive chat interface with a modern design.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.

2. Create a new branch (`git checkout -b feature/YourFeature`).

3. Make your changes and commit them (`git commit -m 'Add some feature'`).

4. Push to the branch (`git push origin feature/YourFeature`).

5. Open a pull request.
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
## Acknowledgments
- [Django](https://www.djangoproject.com/) - The web framework used.
- [Django Channels](https://channels.readthedocs.io/en/stable/) - For handling WebSockets.
- [PostgreSQL](https://www.postgresql.org/) - The database used for storing messages.
- [Redis](https://redis.io/) - For channel layers.
- [Whitenoise](http://whitenoise.evans.io/en/stable/) - For serving static files in production.
- [Python](https://www.python.org/) - The programming language used.