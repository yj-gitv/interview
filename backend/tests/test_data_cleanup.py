from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.position import Position
from app.models.candidate import Candidate
from app.models.interview import Interview, InterviewStatus
from app.models.transcript import Transcript
from app.services.data_cleanup import cleanup_old_data


class TestCleanup:
    def test_deletes_old_completed_interviews(self, db_session: Session):
        pos = Position(title="PM", jd_text="JD")
        db_session.add(pos)
        db_session.flush()

        cand = Candidate(position_id=pos.id, codename="A")
        db_session.add(cand)
        db_session.flush()

        old_interview = Interview(
            position_id=pos.id,
            candidate_id=cand.id,
            status=InterviewStatus.COMPLETED,
            started_at=datetime.now() - timedelta(days=100),
            ended_at=datetime.now() - timedelta(days=100),
        )
        db_session.add(old_interview)
        db_session.flush()

        transcript = Transcript(
            interview_id=old_interview.id,
            speaker="candidate",
            sanitized_text="test",
            timestamp=0.0,
        )
        db_session.add(transcript)
        db_session.commit()

        result = cleanup_old_data(db_session, days=90)
        assert result["interviews"] == 1
        assert result["transcripts"] == 1

    def test_keeps_recent_interviews(self, db_session: Session):
        pos = Position(title="PM", jd_text="JD")
        db_session.add(pos)
        db_session.flush()

        cand = Candidate(position_id=pos.id, codename="B")
        db_session.add(cand)
        db_session.flush()

        recent = Interview(
            position_id=pos.id,
            candidate_id=cand.id,
            status=InterviewStatus.COMPLETED,
            started_at=datetime.now() - timedelta(days=10),
            ended_at=datetime.now() - timedelta(days=10),
        )
        db_session.add(recent)
        db_session.commit()

        result = cleanup_old_data(db_session, days=90)
        assert result["interviews"] == 0

    def test_deletes_old_candidates_without_recent_interviews(
        self, db_session: Session
    ):
        pos = Position(title="PM", jd_text="JD")
        db_session.add(pos)
        db_session.flush()

        old_cand = Candidate(
            position_id=pos.id,
            codename="C",
        )
        db_session.add(old_cand)
        db_session.flush()
        old_cand.created_at = datetime.now() - timedelta(days=100)
        db_session.commit()

        result = cleanup_old_data(db_session, days=90)
        assert result["candidates"] == 1
