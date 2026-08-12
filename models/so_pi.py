from extensions import db
import re


def so_sort_key(code):
    """Kunci urutan natural untuk kode SO (SO1, SO2, ..., SO10, SO11)."""
    match = re.search(r'(\D*)(\d+)', code or '')
    if match:
        return (match.group(1), int(match.group(2)))
    return (code or '', 0)


class StudentOutcome(db.Model):
    """Student Outcome (SO) — capaian lulusan level prodi."""
    __tablename__ = 'student_outcome'

    id             = db.Column(db.Integer, primary_key=True)
    so_code        = db.Column(db.String(20),  nullable=False, unique=True)
    so_description = db.Column(db.Text,        nullable=False)
    is_active      = db.Column(db.Boolean,     nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    indicators = db.relationship(
        'PerformanceIndicator',
        backref='student_outcome',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='PerformanceIndicator.pi_code',
    )

    def __repr__(self):
        return f'<StudentOutcome {self.so_code}>'


class PerformanceIndicator(db.Model):
    """Performance Indicator (PI) — indikator kinerja dari sebuah SO."""
    __tablename__ = 'performance_indicator'
    __table_args__ = (
        db.UniqueConstraint('student_outcome_id', 'pi_code', name='uq_pi_outcome_code'),
    )

    id                 = db.Column(db.Integer, primary_key=True)
    student_outcome_id = db.Column(db.Integer, db.ForeignKey('student_outcome.id'), nullable=False)
    pi_code            = db.Column(db.String(50),  nullable=False)
    pi_description     = db.Column(db.Text,        nullable=False)
    level              = db.Column(db.Integer,     nullable=False, default=1)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<PerformanceIndicator {self.pi_code}>'


class ProficiencyLevel(db.Model):
    """Level proficiency IABEE (1..5) beserta labelnya."""
    __tablename__ = 'proficiency_level'

    level = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<ProficiencyLevel {self.level}: {self.label}>'
