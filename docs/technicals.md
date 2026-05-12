## Equipment Behind the System

*Version 1.0*

Project Pitik is built on a sovereign Free and Open-Source Software (FOSS) stack, intentionally selected to eliminate licensing dependencies, reduce long-term operational costs for LGUs, and ensure full data ownership.

| **Tool(s)/Technology(ies)** | **Description** |
| --- | --- |
| MariaDB | An open-source, high-performance fork of MySQL. It handles all relational data with zero subscription fees and local-first reliability. |
| Tesseract |An industrial-grade OCR engine used to digitize physical permits. It features Zonal Recognition, utilizing fixed coordinate mapping for precision data extraction. |
| OpenCV | Handles image pre-processing and coordinate-based zonal logic, ensuring the system accurately "sees" the specific fields of a document. |
| Opengrep & Codacy | Implements Static Analysis Security Testing (SAST) to audit code quality and prevent data leakages, aligning the system with modern cybersecurity standards. |

### Disclaimers/Notes

**Deployment Flexibility**: The system is designed to be hardware-agnostic. While developed on macOS, the stack is compatible with Windows (via .exe binaries) and Linux-based government workstations.

**Zonal OCR Logic**: Unlike standard OCR that reads entire pages, Pitik uses a Targeted Coordinate System. This reduces "noise" and significantly increases the speed of verification by focusing only on critical permit data fields.

**Cost-Efficiency**: By leveraging open-source binaries (Tesseract/MariaDB) instead of proprietary APIs (Google Vision/AWS RDS), the LGU saves an estimated 100% on recurring software licensing costs.