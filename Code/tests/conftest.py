"""
conftest.py
-----------
Shared pytest fixtures for the AUTOSAR HLD Assistant test suite.
Generates synthetic PDF fixtures programmatically – no confidential documents needed.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Synthetic document content ────────────────────────────────────────────────

SYNTHETIC_HLD_TEXT = """
AUTOSAR High-Level Design – Body Control Module (BCM)
Document Version: 2.1 | ECU Platform: Apex-ECU-300

1. Overview
This document describes the High-Level Design (HLD) of the Body Control Module (BCM)
software for the Apex-ECU-300 platform. The BCM controls interior and exterior lighting,
door locking, window control, and comfort functions.

2. Software Components (SWC)
The following AUTOSAR Software Components are defined:

2.1 LightingManager
The LightingManager SWC controls all exterior and interior lighting functions.
It provides the ExteriorLightPort and InteriorLightPort interfaces.
Signals: LightStatusSignal, LightCommandSignal, DimmingValueSignal.

2.2 DoorLockController
The DoorLockController SWC manages the central locking system.
It depends on the KeyFobSignalReceiver component for authentication signals.
Signals: LockStatusSignal, UnlockRequestSignal, ChildLockSignal.
Interfaces: DoorLockPort (provided), AuthenticationServicePort (required).

2.3 WindowController
The WindowController SWC implements up/down window motor control.
Functional flow: User presses button → WindowCommandSignal generated →
WindowMotorActuator activated → PositionFeedback received → Window stops.
Dependencies: Uses PowerManagementService to check voltage before activation.

2.4 ClimateControlModule
The ClimateControlModule SWC interfaces with HVAC actuators.
It communicates with the TemperatureSensor via the SPI bus.
Signals: TargetTemperatureSignal, ActualTemperatureSignal, FanSpeedSignal.

3. RTE Interfaces
3.1 Inter-Component Communication
Components communicate via the AUTOSAR RTE (Runtime Environment).
The RTE maps ports to signals on the CAN bus and internal virtual function bus (VFB).

Provided ports:
- LightingManager.ExteriorLightPort
- DoorLockController.DoorLockPort
- WindowController.WindowControlPort

Required ports:
- DoorLockController.AuthenticationServicePort (→ KeyFobSignalReceiver)
- WindowController.PowerManagementServicePort (→ PowerManagementService)
- ClimateControlModule.TemperatureSensorPort (→ TemperatureSensor)

4. BSW Configuration
The Basic Software (BSW) stack includes:
- MCAL: ADC, PWM, DIO, SPI, CAN drivers
- COM stack: PDUR, COM, CAN Interface (CANIF)
- OS: AUTOSAR OS with 4 tasks: Task_1ms, Task_10ms, Task_100ms, Task_Background
- DCM: Diagnostic Communication Manager for UDS services
- DEM: Diagnostic Event Manager for fault storage
- NVM: Non-Volatile Memory Manager for configuration data
- Watchdog: Internal watchdog via WDG driver

5. Functional Flows
5.1 Door Lock Sequence
1. KeyFob sends RF signal → KeyFobSignalReceiver decodes
2. AuthenticationService verifies signal hash
3. DoorLockController receives unlock request via UnlockRequestSignal
4. DoorLockController activates door actuators
5. LockStatusSignal updated on CAN bus
6. BCM sends confirmation to IPC cluster

5.2 Lighting Initialization
On startup:
1. ECU initialization (Task_1ms activated)
2. LightingManager reads NVM configuration
3. ExteriorLightPort default state applied
4. DTC cleared if previous fault resolved

6. Dependencies and Interfaces Summary
- LightingManager depends on: NVM, DEM
- DoorLockController depends on: KeyFobSignalReceiver, AuthenticationService, DEM, DCM
- WindowController depends on: PowerManagementService, DEM
- ClimateControlModule depends on: TemperatureSensor, HVAC_Actuator, NVM

7. Signals Summary
CAN signals transmitted by BCM:
- LightStatusSignal (ID: 0x301, 8 bytes, periodic 100ms)
- LockStatusSignal (ID: 0x302, 4 bytes, event-driven)
- WindowStatusSignal (ID: 0x303, 2 bytes, periodic 20ms)
- TemperatureStatusSignal (ID: 0x304, 4 bytes, periodic 500ms)

8. Known Limitations
- The ClimateControlModule fault handling is not yet defined in this revision.
- The KeyFob RF protocol specification is referenced but not included in this document.
- Roll-back mechanism for failed NVM writes is not specified.
"""

SYNTHETIC_HLD_TEXT_V2 = """
AUTOSAR High-Level Design – Body Control Module (BCM) v2.2
Document Version: 2.2 | ECU Platform: Apex-ECU-300

1. Overview (Updated)
Version 2.2 adds the GestureController SWC and revises the WindowController.
The ClimateControlModule has been renamed to ThermalManagementModule.

2. Software Components (SWC)
2.1 LightingManager (unchanged)
Controls all exterior and interior lighting.
Interfaces: ExteriorLightPort, InteriorLightPort.

2.2 DoorLockController (updated)
Now includes biometric authentication via FingerprintSensor.
Signals: LockStatusSignal, UnlockRequestSignal, ChildLockSignal, BiometricSignal.

2.3 WindowController (revised)
Anti-pinch functionality added.
New signals: AntiPinchDetectionSignal, MotorCurrentSignal.

2.4 ThermalManagementModule (renamed from ClimateControlModule)
Expanded scope: now includes battery thermal management.
Signals: TargetTemperatureSignal, BatteryTemperatureSignal, FanSpeedSignal.

2.5 GestureController (new)
Detects hand gestures via ultrasonic sensors.
Signals: GestureCommandSignal, GestureDetectedSignal.
Depends on: UltrasonicSensorArray, LightingManager (for feedback).

3. Removed Components
- KeyFobSignalReceiver is removed; functionality merged into DoorLockController.
"""


def _make_pdf_bytes(text: str, title: str = "Synthetic HLD") -> bytes:
    """Create a minimal valid PDF containing the given text using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))

        for para in text.strip().split("\n\n"):
            para = para.strip()
            if para:
                # Escape special characters for ReportLab
                para_safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                try:
                    story.append(Paragraph(para_safe, styles["Normal"]))
                    story.append(Spacer(1, 0.2 * cm))
                except Exception:
                    pass  # Skip problematic paragraphs

        doc.build(story)
        return buf.getvalue()
    except Exception:
        # Fall back to minimal hand-crafted PDF if reportlab fails
        return _make_minimal_pdf(text)


def _make_minimal_pdf(text: str) -> bytes:
    """Create a bare-bones valid PDF with text content (no external deps)."""
    # Sanitize text for PDF stream
    safe_text = text[:3000].replace("\\", "").replace("(", "").replace(")", "")
    lines = [line[:80] for line in safe_text.split("\n") if line.strip()][:60]

    y = 750
    stream_lines = []
    for line in lines:
        stream_lines.append(f"BT /F1 10 Tf 50 {y} Td ({line}) Tj ET")
        y -= 14
        if y < 50:
            break

    stream_content = "\n".join(stream_lines)
    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        + b"4 0 obj\n<< /Length " + str(stream_len).encode() + b" >>\nstream\n"
        + stream_bytes + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000350 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n420\n%%EOF"
    )
    return pdf


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def synthetic_pdf_bytes():
    """Bytes of a synthetic AUTOSAR HLD PDF (v1)."""
    return _make_pdf_bytes(SYNTHETIC_HLD_TEXT, "BCM HLD v2.1")


@pytest.fixture(scope="session")
def synthetic_pdf_bytes_v2():
    """Bytes of a second synthetic AUTOSAR HLD PDF (v2)."""
    return _make_pdf_bytes(SYNTHETIC_HLD_TEXT_V2, "BCM HLD v2.2")


@pytest.fixture(scope="session")
def synthetic_hld_text():
    return SYNTHETIC_HLD_TEXT


@pytest.fixture(scope="session")
def synthetic_hld_text_v2():
    return SYNTHETIC_HLD_TEXT_V2


@pytest.fixture
def pdf_processor():
    from src.pdf_processor import PDFProcessor
    return PDFProcessor()


@pytest.fixture(scope="session")
def processed_pages(synthetic_pdf_bytes):
    """Returns PageRecord list from the synthetic PDF."""
    from src.pdf_processor import PDFProcessor
    result = PDFProcessor().process_bytes(synthetic_pdf_bytes, "bcm_hld_v2.1.pdf")
    assert result.success, f"Fixture PDF processing failed: {result.error}"
    return result.pages


@pytest.fixture(scope="session")
def text_chunks(processed_pages):
    from src.chunker import TextChunker
    return TextChunker(chunk_size=800, overlap=150).chunk_pages(processed_pages)


@pytest.fixture(scope="session")
def mock_embedder():
    from src.embeddings import EmbeddingModel
    return EmbeddingModel(use_mock=True)


@pytest.fixture(scope="session")
def mock_vector_store(text_chunks, mock_embedder, tmp_path_factory):
    from src.vector_store import VectorStore
    tmp = tmp_path_factory.mktemp("faiss")
    vs = VectorStore(embedding_model=mock_embedder, index_dir=tmp)
    vs.build_index(text_chunks)
    return vs
