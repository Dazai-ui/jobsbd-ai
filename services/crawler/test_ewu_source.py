from sources.ewu_pdf_source import EwuAcademicPdfSource


def test_ewu_policy_pdfs_are_rejected():
    assert not EwuAcademicPdfSource._is_candidate_pdf(
        "https://www.ewubd.edu/storage/app/media/Policies/Grievance%20Policy_2.pdf",
        "Grievance Policy",
    )
    assert not EwuAcademicPdfSource._is_candidate_pdf(
        "https://www.ewubd.edu/storage/app/media/Policies/Plagiarism%20Policy.pdf",
        "Plagiarism Policy",
    )


def test_ewu_public_circular_pdf_is_allowed():
    assert EwuAcademicPdfSource._is_candidate_pdf(
        "https://www.ewubd.edu/storage/app/uploads/public/64a/cec/0dc/64acec0dc2402261617019.pdf",
        "Research Assistant",
    )
