from flask import Flask, render_template, request, send_from_directory, session
import os
from werkzeug.utils import secure_filename
from utils.timetable_generator import generate_dummy_timetable, extract_pdf_text

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated_tts'
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    pdf = request.files['pdf']
    teachers = request.form.getlist('teacher[]')
    subjects = request.form.getlist('subject[]')
    year = request.form.get('year')
    start_time = request.form.get('class_start_time')
    duration = int(request.form.get('class_duration'))
    num_periods = int(request.form.get('num_periods'))

    filename = secure_filename(pdf.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf.save(pdf_path)

    # Extract text from the PDF and generate a summary
    pdf_text = extract_pdf_text(pdf_path)
    summary = "Summary: " + pdf_text[:500]  # Just a snippet for display

    # Map teachers to their subjects
    teacher_subject_map = {teacher.strip(): subject.strip() for teacher, subject in zip(teachers, subjects)}

    # Save to session for regeneration
    session['teacher_subject_map'] = teacher_subject_map
    session['start_time'] = start_time
    session['duration'] = duration
    session['num_periods'] = num_periods

    # Generate timetable using all subjects
    timetable = generate_dummy_timetable(list(teacher_subject_map.values()), num_periods, duration, start_time)

    return render_template('timetable.html', timetable=timetable, summary=summary, regenerate=False)

@app.route('/regenerate', methods=['POST'])
def regenerate():
    unavailable_teachers = [t.strip() for t in request.form.getlist('unavailable_teachers[]') if t.strip()]

    teacher_subject_map = session.get('teacher_subject_map')
    start_time = session.get('start_time')
    duration = session.get('duration')
    num_periods = session.get('num_periods')

    if not all([teacher_subject_map, start_time, duration, num_periods]):
        return "Error: Missing required data from previous submission.", 400

    # Remove subjects of unavailable teachers
    available_subjects = [
        subject for teacher, subject in teacher_subject_map.items()
        if teacher not in unavailable_teachers
    ]

    if not available_subjects:
        return "No available subjects left to generate timetable.", 400

    # Generate new timetable without unavailable teachers
    timetable = generate_dummy_timetable(
        available_subjects,
        int(num_periods),
        int(duration),
        start_time
    )

    return render_template('timetable.html', timetable=timetable, regenerate=True)

if __name__ == '__main__':
    app.run(debug=True)
