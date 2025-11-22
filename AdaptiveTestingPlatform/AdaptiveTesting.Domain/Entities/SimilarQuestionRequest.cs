using System;
using System.Collections.Generic;
using System.Text;

namespace AdaptiveTesting.Domain.Entities {
    public class SimilarQuestionRequest {
        public string FailedQuestionText { get; set; }
        public List<QuestionCandidate> CandidateQuestions { get; set; }
    }
    public record QuestionCandidate(Guid id, string text);
}