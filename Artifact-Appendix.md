# Artifact Appendix (Required for all badges)

Paper title: **AudAgent: Automated Auditing of Privacy Policy Compliance in AI Agents**

Requested Badge(s):
  - [x] **Available**
  - [ ] **Functional**
  - [ ] **Reproduced**

## Description (Required for all badges)

[PETS'26] AudAgent: Automated Auditing of Privacy Policy Compliance in AI Agents.

**Motivation:** Do your AI agents truly honor their privacy promises? As we hand over more autonomy to AI agents, letting them book flights, manage calendars, and even handle payments, we are hitting a critical trust gap. Your agent says it values your privacy, but what is it actually doing with your data when you are not looking?

AudAgent tackles this exact problem. AudAgent provides real-time visibility into potential privacy violations and lets you customize your own privacy preferences so your agents behave the way you control.

### Security/Privacy Issues and Ethical Concerns (Required for all badges)

The artifact does not require any security modifications for installation or execution.

## Environment (Required for all badges)

GitHub repository: https://github.com/ZhengYeah/AudAgent

We do not claim the Functional and Reproduced badges for the following reasons:
- The project requires access to paid LLM APIs for setup and execution, and the framework involves four different LLMs.
- Reproduction of the experiments requires repeated inputs and manual comparison of (potentially) long text/conversations, which is not feasible to automate.

Instead, we provide screen recordings and screenshots in the `README.md` file to demonstrate the two key components described in Section 5.1 and Section 5.2.
## Notes on Reusability (Encouraged for all badges)

The artifact is designed to be reusable and adaptable for a wide range of AI agents and privacy policies.
The core auditing framework is modular, allowing users to integrate different agents, tools, and policy specifications with minimal modification.
Refer to the `examples/` directory for sample scripts that can be easily adapted to new use cases. 