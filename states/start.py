from aiogram.fsm.state import StatesGroup, State

# FSM holatlari
class UserRegistration(StatesGroup):
    position_selection = State()
    full_name = State()
    phone_number = State()
    address = State()
    birth_date = State()
    education = State()
    personal_qualities = State()
    work_experience = State()
    marital_status = State()
    english_level = State()
    russian_level = State()
    salary_expectation = State()
    reference_check = State()
    work_duration = State()
    overtime_work = State()
    work_reasons = State()
    courses_completed = State()
    health_status = State()
    question_some_workers_late_to_work = State()
    question_previous_salary = State()
    question_what_workers_can_thief_answer = State()
    question_what_workers_good_works_some_bad = State()
    about_yourself = State()


    