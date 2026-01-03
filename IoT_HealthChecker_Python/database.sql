CREATE DATABASE IF NOT EXISTS `Do_Name_Checker`;

USE Do_Name_Checker;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  password VARCHAR(255),
  role ENUM('admin','doctor','patient'),
  assigned_doctor_id INT NULL,
  age INT NULL,
  gender ENUM('Male', 'Female', 'Other') NULL
);

CREATE TABLE health_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT,
  temperature FLOAT,
  heart_rate INT,
  spo2 INT,
  bp VARCHAR(20),
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (patient_id) REFERENCES users(id)
);

CREATE TABLE ai_suggestions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT,
  suggestion_text TEXT,
  verified BOOLEAN DEFAULT FALSE,
  doctor_feedback TEXT NULL,
  doctor_status ENUM('Approved', 'Rejected', 'Pending') DEFAULT 'Pending',
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(100) UNIQUE NOT NULL,
  patient_id INT NULL,
  status VARCHAR(50) DEFAULT 'Offline',
  last_upload DATETIME NULL,
  FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE SET NULL
);
