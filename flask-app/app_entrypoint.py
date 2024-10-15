from app import app
import model

if __name__ == '__main__':
    # Initialize the database engine
    engine = model.create_engine('postgresql+psycopg2://user:password@hostname/database_name', echo=True)
    model.create_all()
    
    # Create a scoped session
    app.run(debug=True)