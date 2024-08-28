from src.data.repository import ProducerRepository


class ProducerService:
    def __init__(self, db_session):
        self.repo = ProducerRepository(db_session)