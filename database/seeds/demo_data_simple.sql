-- Demo data for X Hospital (simplified version)

INSERT INTO specialties (id, name, description, pre_visit_instructions) VALUES
(1, 'Cardiology', 'Heart and cardiovascular system treatment', 'Please bring any previous ECG reports, list of current medications, and avoid caffeine 4 hours before appointment.'),
(2, 'Gastroenterology', 'Digestive system and stomach disorders', 'Please do not eat anything for 5 hours before your visit. You may drink water.'),
(3, 'General Medicine', 'Primary care and general health issues', 'Please bring a list of your current medications and any recent test reports.'),
(4, 'Orthopedics', 'Bone, joint, and musculoskeletal treatment', 'Please bring X-ray reports and wear comfortable clothing for physical examination.'),
(5, 'Dermatology', 'Skin, hair, and nail disorders treatment', 'Avoid using makeup or lotions on affected areas before the visit.');

INSERT INTO doctors (id, name, specialty, phone, email) VALUES
(1, 'Dr. Rahman', 'Cardiology', '+8801712345678', 'dr.rahman@xhospital.com'),
(2, 'Dr. Ayesha', 'Gastroenterology', '+8801723456789', 'dr.ayesha@xhospital.com'),
(3, 'Dr. Karim', 'General Medicine', '+8801734567890', 'dr.karim@xhospital.com'),
(4, 'Dr. Fatima', 'Orthopedics', '+8801745678901', 'dr.fatima@xhospital.com'),
(5, 'Dr. Hassan', 'Dermatology', '+8801756789012', 'dr.hassan@xhospital.com');

INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
(1, 1, '18:00:00', '20:00:00'),
(1, 2, '18:00:00', '20:00:00'),
(1, 3, '18:00:00', '20:00:00'),
(1, 4, '18:00:00', '20:00:00'),
(2, 6, '16:00:00', '18:00:00'),
(2, 0, '16:00:00', '18:00:00'),
(2, 1, '16:00:00', '18:00:00'),
(2, 2, '16:00:00', '18:00:00'),
(3, 0, '10:00:00', '14:00:00'),
(3, 1, '10:00:00', '14:00:00'),
(3, 2, '10:00:00', '14:00:00'),
(3, 3, '10:00:00', '14:00:00'),
(3, 4, '10:00:00', '14:00:00'),
(3, 5, '10:00:00', '14:00:00'),
(3, 6, '10:00:00', '14:00:00'),
(4, 1, '14:00:00', '18:00:00'),
(4, 3, '14:00:00', '18:00:00'),
(4, 5, '14:00:00', '18:00:00'),
(5, 2, '09:00:00', '13:00:00'),
(5, 4, '09:00:00', '13:00:00'),
(5, 6, '09:00:00', '13:00:00');

INSERT INTO symptom_mappings (symptom_keywords, specialty_id, priority) VALUES
('["chest pain", "heart pain", "cardiac", "palpitation"]', 1, 3),
('["stomach pain", "abdominal pain", "nausea", "vomiting"]', 2, 3),
('["fever", "cough", "cold", "headache", "general checkup"]', 3, 2),
('["bone pain", "joint pain", "back pain", "fracture"]', 4, 3),
('["skin rash", "acne", "skin allergy", "eczema"]', 5, 3);

INSERT INTO patients (id, name, phone, email, gender, date_of_birth, address) VALUES
(1, 'John Doe', '+8801812345678', 'john.doe@email.com', 'Male', '1985-06-15', 'Dhanmondi, Dhaka'),
(2, 'Jane Smith', '+8801823456789', 'jane.smith@email.com', 'Female', '1990-03-22', 'Gulshan, Dhaka'),
(3, 'Ahmed Hassan', '+8801834567890', 'ahmed.hassan@email.com', 'Male', '1978-11-08', 'Uttara, Dhaka');

INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, symptoms, notes, serial_number, booking_channel, status) VALUES
(1, 1, 1, date('now', '+1 day'), '18:30:00', 'Chest pain and shortness of breath', 'Patient reports chest pain for 2 days', 'XH001', 'chat', 'scheduled'),
(2, 2, 2, date('now', '+2 days'), '16:00:00', 'Stomach pain after meals', 'Gastric issues for 1 week', 'XH002', 'voice', 'scheduled');

INSERT INTO pre_visit_instructions (specialty_id, instruction_text, instruction_type) VALUES
(1, 'Bring your previous ECG reports and cardiac test results', 'documents'),
(1, 'Avoid caffeine and smoking 4 hours before appointment', 'preparation'),
(2, 'Fast for 5 hours before appointment - no food', 'fasting'),
(2, 'You may drink water during fasting period', 'fasting'),
(3, 'Bring current medication list', 'documents'),
(3, 'Bring any recent test reports or medical records', 'documents');

INSERT INTO conversation_history (patient_phone, channel, message_type, message_content, session_id) VALUES
('+8801812345678', 'chat', 'user', 'I have been having chest pain for 2 days', 'session_001'),
('+8801812345678', 'chat', 'assistant', 'I understand you are experiencing chest pain. I recommend seeing our cardiologist, Dr. Rahman.', 'session_001'),
('+8801823456789', 'voice', 'user', 'I need help with stomach problems', 'session_002'),
('+8801823456789', 'voice', 'assistant', 'I can help you with stomach problems. Our gastroenterologist Dr. Ayesha specializes in digestive issues.', 'session_002');