document.addEventListener("DOMContentLoaded", () => {
    const patientText = document.getElementById("patientText");
    const analyzeBtn = document.getElementById("analyzeBtn");

    const loading = document.getElementById("loading");
    const errorSection = document.getElementById("errorSection");
    const errorMessage = document.getElementById("errorMessage");

    const followUpSection = document.getElementById("followUpSection");
    const questionsContainer = document.getElementById("questionsContainer");
    const submitAnswersBtn = document.getElementById("submitAnswersBtn");

    const resultSection = document.getElementById("resultSection");

    const urgency = document.getElementById("urgency");
    const department = document.getElementById("department");
    const ruleId = document.getElementById("ruleId");
    const reasoning = document.getElementById("reasoning");
    const humanReview = document.getElementById("humanReview");

    const patientInfoSection =
        document.getElementById("patientInfoSection");

    const mainComplaint =
        document.getElementById("mainComplaint");

    const reportedSymptoms =
        document.getElementById("reportedSymptoms");

    const remainingUnknowns =
        document.getElementById("remainingUnknowns");

    const finalRuleId =
        document.getElementById("finalRuleId");

    const finalRuleCondition =
        document.getElementById("finalRuleCondition");

    const finalRuleAction =
        document.getElementById("finalRuleAction");

    const finalRuleEscalate =
        document.getElementById("finalRuleEscalate");

    const retrievalSection =
        document.getElementById("retrievalSection");

    const retrievedRules =
        document.getElementById("retrievedRules");

    let currentPatientText = "";
    let currentQuestions = [];

    // =========================================================
    // ERROR FUNCTIONS
    // =========================================================

    function showError(message) {
        if (errorSection) {
            errorSection.classList.remove("hidden");
        }

        if (errorMessage) {
            errorMessage.textContent = message;
        }
    }

    function hideError() {
        if (errorSection) {
            errorSection.classList.add("hidden");
        }

        if (errorMessage) {
            errorMessage.textContent = "";
        }
    }

    // =========================================================
    // LOADING
    // =========================================================

    function showLoading(show) {
        if (!loading) {
            return;
        }

        if (show) {
            loading.classList.remove("hidden");
        } else {
            loading.classList.add("hidden");
        }
    }

    // =========================================================
    // HTML ESCAPE
    // =========================================================

    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // =========================================================
    // QUESTION TYPE
    // =========================================================

    function detectQuestionType(question) {
        const q = String(question || "").toLowerCase();

        // Severity questions
        if (
            q.includes("scale of 1 to 10") ||
            q.includes("1-10") ||
            q.includes("severity")
        ) {
            return "number";
        }

        // Duration questions
        if (
            q.includes("how long") ||
            q.includes("duration") ||
            q.includes("when did")
        ) {
            return "text";
        }

        // Everything else = Yes / No
        return "yes_no";
    }

    function normalizeQuestion(question) {
        if (typeof question === "string") {
            return {
                question: question,
                type: detectQuestionType(question)
            };
        }

        const text =
            question.question ||
            question.text ||
            question.prompt ||
            "";

        return {
            question: text,
            type:
                question.type ||
                detectQuestionType(text),
            id: question.id || null,
            key: question.key || null
        };
    }

    // =========================================================
    // RENDER FOLLOW-UP QUESTIONS
    // =========================================================

    function renderFollowUpQuestions(questions) {
        if (!questionsContainer) {
            return;
        }

        questionsContainer.innerHTML = "";

        if (!questions || questions.length === 0) {
            if (followUpSection) {
                followUpSection.classList.add("hidden");
            }

            return;
        }

        currentQuestions =
            questions.map(normalizeQuestion);

        currentQuestions.forEach((item, index) => {
            const wrapper =
                document.createElement("div");

            wrapper.className = "follow-up-question";

            let inputHtml = "";

            // -------------------------------------------------
            // TEXT QUESTION
            // -------------------------------------------------

            if (item.type === "text") {
                inputHtml = `
                    <input
                        type="text"
                        class="follow-up-input"
                        id="question-${index}"
                        data-question-index="${index}"
                        placeholder="Enter your answer"
                    >
                `;
            }

            // -------------------------------------------------
            // NUMBER QUESTION
            // -------------------------------------------------

            else if (item.type === "number") {
                inputHtml = `
                    <input
                        type="number"
                        class="follow-up-input"
                        id="question-${index}"
                        data-question-index="${index}"
                        min="1"
                        max="10"
                        step="1"
                        placeholder="1 - 10"
                    >
                `;
            }

            // -------------------------------------------------
            // YES / NO QUESTION
            // -------------------------------------------------

            else {
                inputHtml = `
                    <div class="yes-no-options">

                        <label class="radio-option">
                            <input
                                type="radio"
                                name="question-${index}"
                                value="yes"
                                data-question-index="${index}"
                            >
                            <span>Yes</span>
                        </label>

                        <label class="radio-option">
                            <input
                                type="radio"
                                name="question-${index}"
                                value="no"
                                data-question-index="${index}"
                            >
                            <span>No</span>
                        </label>

                    </div>
                `;
            }

            wrapper.innerHTML = `
                <div class="question-number">
                    Question ${index + 1}
                </div>

                <div class="question-text">
                    ${escapeHtml(item.question)}
                </div>

                <div class="question-answer">
                    ${inputHtml}
                </div>
            `;

            questionsContainer.appendChild(wrapper);
        });

        if (followUpSection) {
            followUpSection.classList.remove("hidden");
        }
    }

    // =========================================================
    // COLLECT ANSWERS
    // =========================================================

    function collectAnswers() {
        const answers = [];

        for (
            let i = 0;
            i < currentQuestions.length;
            i++
        ) {
            const item = currentQuestions[i];

            let answer = "";

            // -------------------------------------------------
            // TEXT / NUMBER
            // -------------------------------------------------

            if (
                item.type === "text" ||
                item.type === "number"
            ) {
                const input =
                    document.getElementById(
                        `question-${i}`
                    );

                if (input) {
                    answer = input.value.trim();
                }
            }

            // -------------------------------------------------
            // YES / NO
            // -------------------------------------------------

            else {
                const selected =
                    document.querySelector(
                        `input[name="question-${i}"]:checked`
                    );

                if (selected) {
                    answer = selected.value;
                }
            }

            answers.push({
                question: item.question,
                answer: answer,
                type: item.type
            });
        }

        return answers;
    }

    // =========================================================
    // VALIDATE ANSWERS
    // =========================================================

    function validateAnswers(answers) {
        if (
            !answers ||
            answers.length !== currentQuestions.length
        ) {
            showError(
                "Please answer all follow-up questions."
            );

            return false;
        }

        for (const item of answers) {

            // Empty answer
            if (
                !item.answer ||
                String(item.answer).trim() === ""
            ) {
                showError(
                    "Please answer all follow-up questions."
                );

                return false;
            }

            // Number validation
            if (item.type === "number") {
                const value = Number(item.answer);

                if (
                    Number.isNaN(value) ||
                    value < 1 ||
                    value > 10
                ) {
                    showError(
                        "Please enter a severity value between 1 and 10."
                    );

                    return false;
                }
            }
        }

        return true;
    }

    // =========================================================
    // DISPLAY TRIAGE RESULT
    // =========================================================

    function displayResult(data) {
        if (!data) {
            return;
        }

        const result =
            data.triage_result ||
            data.result ||
            data;

        const recommendedUrgency =
            result.urgency ||
            result.recommended_urgency ||
            "HUMAN_REVIEW";

        const recommendedDepartment =
            result.department ||
            result.recommended_department ||
            "Human Clinical Triage";

        const appliedRule =
            result.rule_id ||
            result.applied_rule ||
            "UN-001";

        const resultReasoning =
            result.reasoning ||
            result.reason ||
            result.condition ||
            "Information is insufficient to safely apply a triage rule.";

        const needsHuman =
            result.human_review !== undefined
                ? result.human_review
                : result.escalate !== undefined
                    ? result.escalate
                    : true;

        // -----------------------------------------------------
        // Main result
        // -----------------------------------------------------

        if (urgency) {
            urgency.textContent =
                recommendedUrgency;
        }

        if (department) {
            department.textContent =
                recommendedDepartment;
        }

        if (ruleId) {
            ruleId.textContent =
                appliedRule;
        }

        if (reasoning) {
            reasoning.textContent =
                resultReasoning;
        }

        if (humanReview) {
            humanReview.textContent =
                needsHuman ? "YES" : "NO";
        }

        // -----------------------------------------------------
        // Patient Information
        // -----------------------------------------------------

        const patientInfo =
            data.patient_information ||
            data.patient_info ||
            {};

        if (mainComplaint) {
            mainComplaint.textContent =
                patientInfo.main_complaint ||
                data.main_complaint ||
                "Not established";
        }

        if (reportedSymptoms) {
            reportedSymptoms.innerHTML = "";

            const symptoms =
                patientInfo.patient_reported ||
                patientInfo.reported_symptoms ||
                data.patient_reported ||
                [];

            if (Array.isArray(symptoms)) {
                symptoms.forEach((symptom) => {
                    const li =
                        document.createElement("li");

                    li.textContent = symptom;

                    reportedSymptoms.appendChild(li);
                });
            }
        }

        if (remainingUnknowns) {
            remainingUnknowns.innerHTML = "";

            const unknowns =
                patientInfo.remaining_unknowns ||
                data.remaining_unknowns ||
                [];

            if (Array.isArray(unknowns)) {
                unknowns.forEach((unknown) => {
                    const li =
                        document.createElement("li");

                    li.textContent = unknown;

                    remainingUnknowns.appendChild(li);
                });
            }
        }

        // -----------------------------------------------------
        // Final Rule
        // -----------------------------------------------------

        const finalRule =
            data.final_rule ||
            data.applied_rule_details ||
            data.rule ||
            {};

        if (finalRuleId) {
            finalRuleId.textContent =
                finalRule.rule_id ||
                appliedRule;
        }

        if (finalRuleCondition) {
            finalRuleCondition.textContent =
                finalRule.condition ||
                result.condition ||
                "";
        }

        if (finalRuleAction) {
            finalRuleAction.textContent =
                finalRule.action ||
                "Human clinical assessment recommended";
        }

        if (finalRuleEscalate) {
            const escalate =
                finalRule.escalate !== undefined
                    ? finalRule.escalate
                    : needsHuman;

            finalRuleEscalate.textContent =
                escalate ? "YES" : "NO";
        }

        // -----------------------------------------------------
        // Retrieved Rules
        // -----------------------------------------------------

        displayRuleEvidence(
            data.retrieved_rules ||
            data.supporting_rules ||
            data.retrieval ||
            []
        );

        if (resultSection) {
            resultSection.classList.remove("hidden");
        }

        if (patientInfoSection) {
            patientInfoSection.classList.remove("hidden");
        }
    }

    // =========================================================
    // DISPLAY RETRIEVED RULES
    // =========================================================

    function displayRuleEvidence(items) {
        if (
            !retrievedRules ||
            !retrievalSection
        ) {
            return;
        }

        retrievedRules.innerHTML = "";

        if (
            !Array.isArray(items) ||
            items.length === 0
        ) {
            retrievalSection.classList.add("hidden");
            return;
        }

        items.forEach((item) => {
            const rule =
                item.rule || {};

            const card =
                document.createElement("div");

            card.className =
                "retrieved-rule-card";

            const similarity =
                item.similarity !== undefined
                    ? Number(item.similarity).toFixed(4)
                    : "N/A";

            card.innerHTML = `
                <h3>
                    ${escapeHtml(
                        rule.rule_id ||
                        item.rule_id ||
                        "Rule"
                    )}
                </h3>

                <p>
                    <strong>Condition:</strong>
                    ${escapeHtml(
                        rule.condition || ""
                    )}
                </p>

                <p>
                    <strong>Urgency:</strong>
                    ${escapeHtml(
                        rule.urgency || ""
                    )}
                </p>

                <p>
                    <strong>Department:</strong>
                    ${escapeHtml(
                        rule.department || ""
                    )}
                </p>

                <p>
                    <strong>Action:</strong>
                    ${escapeHtml(
                        rule.action || ""
                    )}
                </p>

                <p>
                    <strong>Similarity:</strong>
                    ${similarity}
                </p>
            `;

            retrievedRules.appendChild(card);
        });

        retrievalSection.classList.remove("hidden");
    }

    // =========================================================
    // ANALYZE PATIENT
    // =========================================================

    async function analyzePatient() {
        hideError();

        const text =
            patientText
                ? patientText.value.trim()
                : "";

        if (!text) {
            showError(
                "Please enter the patient's symptoms."
            );

            return;
        }

        currentPatientText = text;

        showLoading(true);

        if (followUpSection) {
            followUpSection.classList.add("hidden");
        }

        if (resultSection) {
            resultSection.classList.add("hidden");
        }

        try {
            const response =
                await fetch("/api/analyze", {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        patient_text: text,
                        answers: {}
                    })
                });

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "Unable to analyze the patient."
                );
            }

            const questions =
                data.follow_up_questions ||
                data.followup_questions ||
                data.questions ||
                [];

            // -------------------------------------------------
            // Follow-up questions available
            // -------------------------------------------------

            if (
                Array.isArray(questions) &&
                questions.length > 0
            ) {
                renderFollowUpQuestions(
                    questions
                );

                displayResult(data);

                return;
            }

            // -------------------------------------------------
            // Direct result
            // -------------------------------------------------

            displayResult(data);

        } catch (error) {
            console.error(
                "Analyze error:",
                error
            );

            showError(
                error.message ||
                "Something went wrong while analyzing the patient."
            );

        } finally {
            showLoading(false);
        }
    }

    // =========================================================
    // SUBMIT FOLLOW-UP ANSWERS
    // =========================================================

    async function submitAnswers() {
        hideError();

        const answers =
            collectAnswers();

        // IMPORTANT:
        // Validate every question
        if (!validateAnswers(answers)) {
            return;
        }

        showLoading(true);

        if (submitAnswersBtn) {
            submitAnswersBtn.disabled = true;
            submitAnswersBtn.textContent =
                "Analyzing...";
        }

        try {
            const response =
                await fetch("/api/analyze", {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        patient_text:
                            currentPatientText,

                        answers:
                            answers
                    })
                });

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "Unable to process the follow-up answers."
                );
            }

            // Display final result
            displayResult(data);

            // Hide questions
            if (followUpSection) {
                followUpSection.classList.add(
                    "hidden"
                );
            }

            // Scroll to result
            if (resultSection) {
                resultSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }

        } catch (error) {
            console.error(
                "Follow-up error:",
                error
            );

            showError(
                error.message ||
                "Something went wrong while processing the answers."
            );

        } finally {
            showLoading(false);

            if (submitAnswersBtn) {
                submitAnswersBtn.disabled = false;
                submitAnswersBtn.textContent =
                    "Submit Answers";
            }
        }
    }

    // =========================================================
    // BUTTON EVENTS
    // =========================================================

    if (analyzeBtn) {
        analyzeBtn.addEventListener(
            "click",
            analyzePatient
        );
    }

    if (submitAnswersBtn) {
        submitAnswersBtn.addEventListener(
            "click",
            submitAnswers
        );
    }

    // =========================================================
    // CMD + ENTER / CTRL + ENTER
    // =========================================================

    if (patientText) {
        patientText.addEventListener(
            "keydown",
            (event) => {

                if (
                    (event.ctrlKey ||
                        event.metaKey) &&
                    event.key === "Enter"
                ) {
                    analyzePatient();
                }

            }
        );
    }
});