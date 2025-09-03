-- Demo data for X Hospital

-- Insert specialties
INSERT INTO specialties (id, name, description, pre_visit_instructions) VALUES
(1, 'Cardiology', 'Heart and cardiovascular system treatment', 'Please bring any previous ECG reports, list of current medications, and avoid caffeine 4 hours before appointment.'),
(2, 'Gastroenterology', 'Digestive system and stomach disorders', 'Please do not eat anything for 5 hours before your visit. You may drink water.'),
(3, 'General Medicine', 'Primary care and general health issues', 'Please bring a list of your current medications and any recent test reports.'),
(4, 'Orthopedics', 'Bone, joint, and musculoskeletal treatment', 'Please bring X-ray reports and wear comfortable clothing for physical examination.'),
(5, 'Dermatology', 'Skin, hair, and nail disorders treatment', 'Avoid using makeup or lotions on affected areas before the visit.'),
(6, 'ENT', 'Ear, Nose, and Throat specialist', 'Please avoid eating or drinking 2 hours before throat examination.'),
(7, 'Neurology', 'Brain and nervous system disorders', 'Bring any brain scan reports and list of current medications.'),
(8, 'Pediatrics', 'Child healthcare and development', 'Bring vaccination records and growth charts for children.'),
(9, 'Gynecology', 'Women reproductive health', 'Schedule appointment avoiding menstrual period if possible.'),
(10, 'Urology', 'Urinary tract and male reproductive system', 'Bring recent urine test reports if available.');

-- Insert doctors
INSERT INTO doctors (id, name, specialty, phone, email) VALUES
(1, 'Dr. Rahman', 'Cardiology', '+8801712345678', 'dr.rahman@xhospital.com'),
(2, 'Dr. Ayesha', 'Gastroenterology', '+8801723456789', 'dr.ayesha@xhospital.com'),
(3, 'Dr. Karim', 'General Medicine', '+8801734567890', 'dr.karim@xhospital.com'),
(4, 'Dr. Fatima', 'Orthopedics', '+8801745678901', 'dr.fatima@xhospital.com'),
(5, 'Dr. Hassan', 'Dermatology', '+8801756789012', 'dr.hassan@xhospital.com'),
(6, 'Dr. Nasir', 'ENT', '+8801767890123', 'dr.nasir@xhospital.com'),
(7, 'Dr. Zara', 'Neurology', '+8801778901234', 'dr.zara@xhospital.com'),
(8, 'Dr. Marium', 'Pediatrics', '+8801789012345', 'dr.marium@xhospital.com'),
(9, 'Dr. Rashida', 'Gynecology', '+8801790123456', 'dr.rashida@xhospital.com'),
(10, 'Dr. Tariq', 'Urology', '+8801701234567', 'dr.tariq@xhospital.com'),
(11, 'Dr. Salam', 'General Medicine', '+8801712345679', 'dr.salam@xhospital.com'),
(12, 'Dr. Nadia', 'Cardiology', '+8801723456780', 'dr.nadia@xhospital.com');

-- Insert doctor schedules
-- Dr. Rahman (Cardiologist): Mon–Thu, 6:00 PM – 8:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(1, 1, '18:00:00', '20:00:00'), -- Monday
(1, 2, '18:00:00', '20:00:00'), -- Tuesday
(1, 3, '18:00:00', '20:00:00'), -- Wednesday
(1, 4, '18:00:00', '20:00:00'); -- Thursday

-- Dr. Ayesha (Gastroenterologist): Sat–Tue, 4:00 PM – 6:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(2, 6, '16:00:00', '18:00:00'), -- Saturday
(2, 0, '16:00:00', '18:00:00'), -- Sunday
(2, 1, '16:00:00', '18:00:00'), -- Monday
(2, 2, '16:00:00', '18:00:00'); -- Tuesday

-- Dr. Karim (General Physician): Every day, 10:00 AM – 2:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(3, 0, '10:00:00', '14:00:00'), -- Sunday
(3, 1, '10:00:00', '14:00:00'), -- Monday
(3, 2, '10:00:00', '14:00:00'), -- Tuesday
(3, 3, '10:00:00', '14:00:00'), -- Wednesday
(3, 4, '10:00:00', '14:00:00'), -- Thursday
(3, 5, '10:00:00', '14:00:00'), -- Friday
(3, 6, '10:00:00', '14:00:00'), -- Saturday

-- Dr. Fatima (Orthopedics): Mon, Wed, Fri, 2:00 PM – 6:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(4, 1, '14:00:00', '18:00:00'), -- Monday
(4, 3, '14:00:00', '18:00:00'), -- Wednesday
(4, 5, '14:00:00', '18:00:00'); -- Friday

-- Dr. Hassan (Dermatology): Tue, Thu, Sat, 9:00 AM – 1:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(5, 2, '09:00:00', '13:00:00'), -- Tuesday
(5, 4, '09:00:00', '13:00:00'), -- Thursday
(5, 6, '09:00:00', '13:00:00'); -- Saturday

-- Dr. Nasir (ENT): Mon–Fri, 3:00 PM – 7:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(6, 1, '15:00:00', '19:00:00'), -- Monday
(6, 2, '15:00:00', '19:00:00'), -- Tuesday
(6, 3, '15:00:00', '19:00:00'), -- Wednesday
(6, 4, '15:00:00', '19:00:00'), -- Thursday
(6, 5, '15:00:00', '19:00:00'); -- Friday

-- Dr. Zara (Neurology): Tue, Thu, 5:00 PM – 8:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(7, 2, '17:00:00', '20:00:00'), -- Tuesday
(7, 4, '17:00:00', '20:00:00'); -- Thursday

-- Dr. Marium (Pediatrics): Mon–Sat, 8:00 AM – 12:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(8, 1, '08:00:00', '12:00:00'), -- Monday
(8, 2, '08:00:00', '12:00:00'), -- Tuesday
(8, 3, '08:00:00', '12:00:00'), -- Wednesday
(8, 4, '08:00:00', '12:00:00'), -- Thursday
(8, 5, '08:00:00', '12:00:00'), -- Friday
(8, 6, '08:00:00', '12:00:00'); -- Saturday

-- Dr. Rashida (Gynecology): Mon, Wed, Fri, 4:00 PM – 7:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(9, 1, '16:00:00', '19:00:00'), -- Monday
(9, 3, '16:00:00', '19:00:00'), -- Wednesday
(9, 5, '16:00:00', '19:00:00'); -- Friday

-- Dr. Tariq (Urology): Sun, Tue, Thu, 11:00 AM – 3:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(10, 0, '11:00:00', '15:00:00'), -- Sunday
(10, 2, '11:00:00', '15:00:00'), -- Tuesday
(10, 4, '11:00:00', '15:00:00'); -- Thursday

-- Dr. Salam (General Medicine): Every day, 6:00 PM – 10:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(11, 0, '18:00:00', '22:00:00'), -- Sunday
(11, 1, '18:00:00', '22:00:00'), -- Monday
(11, 2, '18:00:00', '22:00:00'), -- Tuesday
(11, 3, '18:00:00', '22:00:00'), -- Wednesday
(11, 4, '18:00:00', '22:00:00'), -- Thursday
(11, 5, '18:00:00', '22:00:00'), -- Friday
(11, 6, '18:00:00', '22:00:00'); -- Saturday

-- Dr. Nadia (Cardiology): Sat–Mon, 1:00 PM – 5:00 PM
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(12, 6, '13:00:00', '17:00:00'), -- Saturday
(12, 0, '13:00:00', '17:00:00'), -- Sunday
(12, 1, '13:00:00', '17:00:00'); -- Monday

-- Insert symptom mappings
INSERT INTO symptom_mappings (symptom_keywords, specialty_id, priority) VALUES
-- Cardiology
('["chest pain", "heart pain", "cardiac", "palpitation", "chest tightness", "heart rate", "blood pressure"]', 1, 3),
('["shortness of breath", "breathing problem", "chest pain"]', 1, 2),
('["high blood pressure", "hypertension", "irregular heartbeat", "heart attack", "chest pressure"]', 1, 3),

-- Gastroenterology
('["stomach pain", "abdominal pain", "nausea", "vomiting", "diarrhea", "constipation", "acid reflux", "heartburn", "gastric"]', 2, 3),
('["loss of appetite", "weight loss", "bloating", "gas"]', 2, 2),
('["liver pain", "jaundice", "yellow eyes", "hepatitis", "ulcer", "food poisoning"]', 2, 3),

-- General Medicine
('["fever", "cough", "cold", "headache", "body ache", "flu", "sore throat", "weakness", "fatigue", "general checkup"]', 3, 2),
('["diabetes", "blood sugar", "high sugar", "diabetes check", "routine checkup", "health screening"]', 3, 2),

-- Orthopedics
('["bone pain", "joint pain", "back pain", "neck pain", "shoulder pain", "knee pain", "fracture", "sprain"]', 4, 3),
('["arthritis", "muscle pain", "stiffness", "swelling in joints", "hip pain", "ankle pain"]', 4, 2),
('["sports injury", "broken bone", "dislocation", "torn ligament", "muscle strain"]', 4, 3),

-- Dermatology
('["skin rash", "itching", "acne", "skin allergy", "eczema", "psoriasis", "moles", "skin spots"]', 5, 3),
('["hair fall", "baldness", "dandruff", "nail problems", "fungal infection", "warts"]', 5, 2),
('["skin cancer", "suspicious mole", "skin growth", "pigmentation", "dark spots"]', 5, 3),

-- ENT
('["ear pain", "hearing loss", "tinnitus", "ear infection", "wax blockage", "ear discharge"]', 6, 3),
('["nose bleeding", "sinusitis", "nasal congestion", "smell loss", "deviated septum"]', 6, 2),
('["throat pain", "voice hoarseness", "tonsillitis", "difficulty swallowing", "vocal problems"]', 6, 3),

-- Neurology
('["severe headache", "migraine", "seizure", "epilepsy", "memory loss", "confusion"]', 7, 3),
('["numbness", "tingling", "paralysis", "stroke symptoms", "tremors", "coordination problems"]', 7, 3),
('["dizziness", "balance problems", "fainting", "brain fog", "concentration problems"]', 7, 2),

-- Pediatrics
('["child fever", "baby cough", "vaccination", "growth problems", "development delay"]', 8, 3),
('["child not eating", "crying continuously", "sleep problems", "behavioral issues"]', 8, 2),
('["rash in baby", "diaper rash", "child injury", "accident", "poisoning"]', 8, 3),

-- Gynecology
('["menstrual problems", "irregular periods", "heavy bleeding", "period pain", "PCOS"]', 9, 3),
('["pregnancy symptoms", "morning sickness", "prenatal care", "fertility issues", "contraception"]', 9, 2),
('["vaginal infection", "UTI", "breast pain", "ovarian pain", "menopause symptoms"]', 9, 3),

-- Urology
('["kidney stone", "painful urination", "blood in urine", "frequent urination", "kidney pain"]', 10, 3),
('["prostate problems", "erectile dysfunction", "male infertility", "testicular pain"]', 10, 2),
('["bladder infection", "incontinence", "urinary tract infection", "kidney infection"]', 10, 3);

-- Insert pre-visit instructions
INSERT INTO pre_visit_instructions (specialty_id, instruction_text, instruction_type) VALUES
-- Cardiology
(1, 'Bring your previous ECG reports and cardiac test results', 'documents'),
(1, 'List all current medications including dosages', 'preparation'),
(1, 'Avoid caffeine and smoking 4 hours before appointment', 'preparation'),

-- Gastroenterology
(2, 'Fast for 5 hours before appointment - no food', 'fasting'),
(2, 'You may drink water during fasting period', 'fasting'),
(2, 'Bring list of current medications', 'documents'),

-- General Medicine
(3, 'Bring current medication list', 'documents'),
(3, 'Bring any recent test reports or medical records', 'documents'),

-- Orthopedics
(4, 'Bring X-ray reports and previous imaging studies', 'documents'),
(4, 'Wear comfortable clothing for physical examination', 'preparation'),
(4, 'Bring list of pain medications currently taking', 'documents'),

-- Dermatology
(5, 'Avoid using makeup or lotions on affected skin areas', 'preparation'),
(5, 'Bring photos of skin changes if applicable', 'documents'),
(5, 'List any skin products or medications currently using', 'preparation'),

-- ENT
(6, 'Avoid eating or drinking 2 hours before throat examination', 'fasting'),
(6, 'Bring hearing test reports if available', 'documents'),
(6, 'List any ear drops or nasal medications used', 'preparation'),

-- Neurology
(7, 'Bring brain scan reports (CT, MRI) if available', 'documents'),
(7, 'List all current medications and supplements', 'documents'),
(7, 'Keep a symptom diary before visit if possible', 'preparation'),

-- Pediatrics
(8, 'Bring vaccination records and growth charts', 'documents'),
(8, 'Bring favorite toy or comfort item for child', 'preparation'),
(8, 'List all medications and allergies', 'documents'),

-- Gynecology
(9, 'Schedule appointment avoiding menstrual period if possible', 'preparation'),
(9, 'Bring previous gynecological reports', 'documents'),
(9, 'List menstrual cycle dates and contraceptive methods', 'preparation'),

-- Urology
(10, 'Bring recent urine test reports if available', 'documents'),
(10, 'Drink plenty of water before urine tests', 'preparation'),
(10, 'List any urinary medications or supplements', 'documents');

-- Insert sample patients
INSERT INTO patients (id, name, phone, email, gender, date_of_birth, address) VALUES
(1, 'John Doe', '+8801812345678', 'john.doe@email.com', 'Male', '1985-06-15', 'Dhanmondi, Dhaka'),
(2, 'Jane Smith', '+8801823456789', 'jane.smith@email.com', 'Female', '1990-03-22', 'Gulshan, Dhaka'),
(3, 'Ahmed Hassan', '+8801834567890', 'ahmed.hassan@email.com', 'Male', '1978-11-08', 'Uttara, Dhaka'),
(4, 'Fatima Khatun', '+8801845678901', 'fatima.khatun@email.com', 'Female', '1992-07-30', 'Mirpur, Dhaka'),
(5, 'Mohammad Ali', '+8801856789012', 'mohammad.ali@email.com', 'Male', '1987-02-14', 'Wari, Dhaka'),
(6, 'Rashida Begum', '+8801867890123', 'rashida.begum@email.com', 'Female', '1995-09-18', 'Banani, Dhaka'),
(7, 'Karim Rahman', '+8801878901234', 'karim.rahman@email.com', 'Male', '1982-12-03', 'Motijheel, Dhaka'),
(8, 'Nasreen Akter', '+8801889012345', 'nasreen.akter@email.com', 'Female', '1988-05-25', 'Tejgaon, Dhaka'),
(9, 'Rahim Uddin', '+8801890123456', 'rahim.uddin@email.com', 'Male', '1975-01-10', 'Old Dhaka'),
(10, 'Salma Khatun', '+8801801234567', 'salma.khatun@email.com', 'Female', '1993-08-12', 'Bashundhara, Dhaka'),
(11, 'Tariq Ahmed', '+8801812345679', 'tariq.ahmed@email.com', 'Male', '1980-04-20', 'Lalmatia, Dhaka'),
(12, 'Ruma Begum', '+8801823456780', 'ruma.begum@email.com', 'Female', '1991-10-05', 'Mohammadpur, Dhaka');

-- Sample appointments - realistic scenarios
INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, symptoms, notes, serial_number, booking_channel, status) VALUES
-- Scheduled appointments
(1, 1, 1, date('now', '+1 day'), '18:30:00', 'Chest pain and shortness of breath', 'Patient reports chest pain for 2 days', 'XH001', 'chat', 'scheduled'),
(2, 2, 2, date('now', '+2 days'), '16:00:00', 'Stomach pain after meals', 'Gastric issues for 1 week', 'XH002', 'voice', 'scheduled'),
(3, 3, 4, date('now', '+1 day'), '14:30:00', 'Lower back pain', 'Back pain from heavy lifting', 'XH003', 'chat', 'scheduled'),
(4, 4, 5, date('now', '+3 days'), '09:30:00', 'Skin rash on arms', 'Rash appeared 3 days ago', 'XH004', 'voice', 'scheduled'),
(5, 5, 6, date('now', '+2 days'), '15:30:00', 'Ear pain and hearing difficulty', 'Pain started yesterday', 'XH005', 'chat', 'scheduled'),
(6, 6, 8, date('now', '+1 day'), '08:30:00', 'Child fever for 2 days', 'Bringing 5-year-old son', 'XH006', 'voice', 'scheduled'),
(7, 7, 3, date('now', '+1 day'), '10:30:00', 'General checkup and diabetes monitoring', 'Routine checkup', 'XH007', 'chat', 'scheduled'),
(8, 8, 9, date('now', '+4 days'), '16:30:00', 'Irregular menstrual periods', 'PCOS consultation', 'XH008', 'voice', 'scheduled'),
(9, 9, 10, date('now', '+3 days'), '11:30:00', 'Kidney stone symptoms', 'Severe abdominal pain', 'XH009', 'chat', 'scheduled'),
(10, 10, 7, date('now', '+5 days'), '17:30:00', 'Severe headaches and dizziness', 'Migraine symptoms', 'XH010', 'voice', 'scheduled'),

-- Completed appointments (past)
(11, 1, 12, date('now', '-2 days'), '13:30:00', 'Chest pain follow-up', 'ECG normal, prescribed medication', 'XH011', 'chat', 'completed'),
(12, 3, 3, date('now', '-5 days'), '11:00:00', 'Routine health checkup', 'All vitals normal', 'XH012', 'voice', 'completed'),
(13, 5, 2, date('now', '-3 days'), '16:30:00', 'Stomach upset', 'Prescribed antacids', 'XH013', 'chat', 'completed'),

-- Cancelled appointments
(14, 11, 1, date('now', '+6 days'), '19:00:00', 'Chest pain consultation', 'Patient cancelled due to travel', 'XH014', 'voice', 'cancelled'),

-- No-show appointments
(15, 12, 4, date('now', '-1 day'), '15:00:00', 'Joint pain consultation', 'Patient did not show up', 'XH015', 'chat', 'no_show');

-- Sample conversation history
INSERT INTO conversation_history (patient_phone, channel, message_type, message_content, session_id) VALUES
-- Chat conversation - Chest pain case
('+8801812345678', 'chat', 'user', 'Hello, I have been having chest pain for 2 days', 'session_001'),
('+8801812345678', 'chat', 'assistant', 'Hello! I understand you are experiencing chest pain for 2 days. This could be related to your heart. Can you describe the pain? Is it sharp, dull, or crushing?', 'session_001'),
('+8801812345678', 'chat', 'user', 'Its a sharp pain, especially when I breathe deeply', 'session_001'),
('+8801812345678', 'chat', 'assistant', 'I recommend seeing our cardiologist. We have Dr. Rahman available Mon-Thu 6-8 PM and Dr. Nadia available Sat-Mon 1-5 PM. Which would you prefer?', 'session_001'),
('+8801812345678', 'chat', 'user', 'Dr. Rahman sounds good. When is his next available slot?', 'session_001'),
('+8801812345678', 'chat', 'assistant', 'Dr. Rahman has an available slot tomorrow at 6:30 PM. Would you like me to book this for you? I will need your full name to confirm.', 'session_001'),
('+8801812345678', 'chat', 'user', 'Yes please. My name is John Doe', 'session_001'),
('+8801812345678', 'chat', 'assistant', 'Perfect! I have booked your appointment with Dr. Rahman for tomorrow at 6:30 PM. Your serial number is XH001. Please bring previous ECG reports and avoid caffeine 4 hours before appointment.', 'session_001'),

-- Voice conversation - Stomach problems
('+8801823456789', 'voice', 'user', 'I need help with stomach problems', 'session_002'),
('+8801823456789', 'voice', 'assistant', 'I can help you with stomach problems. Our gastroenterologist Dr. Ayesha specializes in digestive issues. Can you tell me more about your symptoms?', 'session_002'),
('+8801823456789', 'voice', 'user', 'I have stomach pain after eating, especially spicy food', 'session_002'),
('+8801823456789', 'voice', 'assistant', 'That sounds like it could be gastritis or acid reflux. Dr. Ayesha is available Sat-Tue from 4-6 PM. When would be convenient for you?', 'session_002'),
('+8801823456789', 'voice', 'user', 'This Saturday would be good', 'session_002'),
('+8801823456789', 'voice', 'assistant', 'Great! Dr. Ayesha has availability this Saturday at 4:00 PM. May I have your name to book this appointment?', 'session_002'),
('+8801823456789', 'voice', 'user', 'Jane Smith', 'session_002'),
('+8801823456789', 'voice', 'assistant', 'Thank you Jane. Your appointment is confirmed for Saturday at 4:00 PM with Dr. Ayesha. Serial number XH002. Please fast for 5 hours before the appointment - you may drink water. See you Saturday!', 'session_002'),

-- Chat conversation - Back pain case
('+8801834567890', 'chat', 'user', 'I hurt my back lifting heavy boxes at work', 'session_003'),
('+8801834567890', 'chat', 'assistant', 'I am sorry to hear about your back injury. Back pain from heavy lifting is quite common. This sounds like an orthopedic issue. Our Dr. Fatima specializes in bone and joint problems.', 'session_003'),
('+8801834567890', 'chat', 'user', 'How bad is the pain on a scale of 1-10?', 'session_003'),
('+8801834567890', 'chat', 'assistant', 'That is a good question to assess the severity. On a scale of 1-10, how would you rate your current pain level? Also, can you walk normally or is movement difficult?', 'session_003'),
('+8801834567890', 'chat', 'user', 'About 7 out of 10, and walking is painful', 'session_003'),
('+8801834567890', 'chat', 'assistant', 'That is significant pain. I recommend seeing Dr. Fatima soon. She is available Monday, Wednesday, and Friday from 2-6 PM. The earliest would be tomorrow at 2:30 PM. Shall I book this for you?', 'session_003'),
('+8801834567890', 'chat', 'user', 'Yes please, Ahmed Hassan', 'session_003'),
('+8801834567890', 'chat', 'assistant', 'Booked! Ahmed Hassan, tomorrow 2:30 PM with Dr. Fatima. Serial XH003. Please bring any X-ray reports and wear comfortable clothing for examination. Take care!', 'session_003'),

-- Voice conversation - Child fever
('+8801845678901', 'voice', 'user', 'My child has fever for 2 days, I am worried', 'session_004'),
('+8801845678901', 'voice', 'assistant', 'I understand your concern about your child having fever for 2 days. Children and fever always need attention. How old is your child and what is the fever temperature?', 'session_004'),
('+8801845678901', 'voice', 'user', 'He is 5 years old and fever is 102 degrees', 'session_004'),
('+8801845678901', 'voice', 'assistant', 'A 102-degree fever in a 5-year-old does need medical attention. Our pediatrician Dr. Marium is excellent with children. She is available Monday through Saturday from 8 AM to 12 PM. Would you like an appointment today?', 'session_004'),
('+8801845678901', 'voice', 'user', 'Yes, as soon as possible please', 'session_004'),
('+8801845678901', 'voice', 'assistant', 'I can get you in tomorrow morning at 8:30 AM with Dr. Marium. May I have your name to book this urgent appointment?', 'session_004'),
('+8801845678901', 'voice', 'user', 'Fatima Khatun', 'session_004'),
('+8801845678901', 'voice', 'assistant', 'Done! Fatima Khatun, tomorrow 8:30 AM with Dr. Marium for your 5-year-old son. Serial XH006. Please bring vaccination records and a favorite toy for comfort. Monitor the fever tonight.', 'session_004'),

-- Chat conversation - Routine checkup
('+8801878901234', 'chat', 'user', 'I need a routine checkup for diabetes monitoring', 'session_005'),
('+8801878901234', 'chat', 'assistant', 'Routine diabetes monitoring is very important for maintaining good health. Our general medicine doctors can help with this. Dr. Karim is available daily 10 AM-2 PM or Dr. Salam is available daily 6-10 PM.', 'session_005'),
('+8801878901234', 'chat', 'user', 'Morning time works better for me', 'session_005'),
('+8801878901234', 'chat', 'assistant', 'Perfect! Dr. Karim has morning availability. He can see you tomorrow at 10:30 AM for your diabetes checkup. What is your name?', 'session_005'),
('+8801878901234', 'chat', 'user', 'Karim Rahman', 'session_005'),
('+8801878901234', 'chat', 'assistant', 'Great! Karim Rahman, tomorrow 10:30 AM with Dr. Karim. Serial XH007. Please bring your current medication list and any recent test reports. Fasting is recommended for accurate blood sugar tests.', 'session_005');