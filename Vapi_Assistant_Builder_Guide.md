# Vapi Assistant Builder

## Purpose

The Vapi Assistant Builder is designed to enable Account Executives (AEs) to update and customize voice bots built on Vapi for demo purposes. It aims to reduce the sales team's dependency on the Product team for small, routine changes such as updating customer names, client names, or dates, allowing AEs to tailor demos quickly and efficiently.

## Features :

The **Assistant Builder** enables AEs to create and customize assistants based on their specific demo or client needs. It provides the following capabilities:

- **Variable Configuration :** Similar to variable setup in LLM Studio, AEs can view and edit assistant variables to tailor behavior and responses.

- **Explain-Due Messaging Customization :** AEs can refine how the assistant explains the outstanding balance by adjusting tone, structure, or the entire message. Messaging can be generated using AI or manually edited to better suit the demo context.

- **FAQ Creation and Management :** AEs can view existing FAQs and generate new ones using AI, leveraging prompts defined and trained by the product team.

- **Assistant Retention Period :** To prevent unused demo assistants from accumulating in Vapi, assistants created through this tool are automatically deleted after two weeks. AEs can optionally extend the retention period if the assistant needs to be reused.

## Login and Registration :

To access the app, users must register and log in. New users can create an account using their **email address** or by signing in with **Google**.

---

## Bot Creation :

When creating bots, AEs are required to configure essential details such as **assistant variables** to ensure the bot functions correctly. In addition, AEs have the flexibility to customize other aspects of the assistant, such as **FAQs** and **Explain Due messaging** to better align with the demo or client requirements.

The **dropdown menu** displays all available bots that can be edited. AEs can select the appropriate bot based on their needs. For any questions about the flows supported by a particular bot, please refer to the Demo Bots Database.

The steps and available configuration options for making these updates are outlined below.

---

## Variable Updation :

Variables differ based on the selected bot and the workflow it supports. To ensure a smooth and error-free experience, all required variables must be filled in.

### Steps to update variables

1. **Review available variables**

   Once a bot is selected, review the list of variables displayed for that bot and its supported workflow.

2. **Fill in all required values**

   Enter values for **every variable shown**. Missing or incomplete variables may cause issues during bot execution or break the flow.

3. **Update variables**

   After entering all values, click the **"Update Variables"** button to save your changes.

---

## Explain Due Message Customization :

AEs can customize the **Explain Due** message to match the product being demoed and the intended tone of the conversation. The message can be updated either by pasting custom content or by generating a new version using AI.

### Steps to customize the Explain Due message

1. **Select an update method**

   Choose whether to **paste a custom Explain Due message** or **generate one using AI**.

2. **Generate using AI (optional)**

   If generating with AI, specify the desired tone, style, or phrasing (e.g., professional, empathetic, concise). The system will generate a draft message based on your input.

3. **Review the message**

   The generated or pasted message is displayed for review. The AE can choose to **"Use this message"** or **"Discard."**

4. **Apply changes**

   If **"Use this message"** is selected, the updated Explain Due message replaces the existing message and is saved for use by the assistant.

---

## FAQ Generation :

AEs can add custom FAQs to handle specific questions that callers might ask during a demo. The system uses AI to convert your FAQ inputs into a properly formatted prompt.

### Steps to add and generate FAQs

1. **View existing FAQs**

   Expand the **"View Existing FAQ Context"** section to see FAQs already configured in the selected bot.

2. **Add custom FAQs**

   Expand **"Optional: Add Custom FAQs"** and fill in:
   - **Question the user will ask** — The question or phrase the caller might say
   - **How you want the bot to respond** — The desired response behavior

   Click **"Add FAQ"** to save each FAQ entry.

3. **Edit or delete FAQs**

   Use the **"Edit"** button to modify an existing FAQ or **"Delete"** to remove it.

4. **Generate FAQ prompt**

   Once all FAQs are added, click **"Generate FAQ Prompt"**. The AI will create a formatted prompt based on your inputs.

5. **Review and regenerate (optional)**

   Review the generated prompt. Click **"Regenerate"** if you want a different version.

---

## Assistant Creation :

Once all customizations are complete, AEs can create a new assistant with the updated configuration.

### Steps to create a new assistant

1. **Enter assistant name**

   Provide a unique name for the new assistant in the **"Assistant Name"** field. This name will be used to identify the assistant in VAPI.

2. **Select retention period**

   Choose how long to keep the assistant before automatic deletion:
   - 2 weeks (default)
   - 3 weeks
   - 4 weeks
   - 5 weeks
   - 6 weeks

3. **Create the assistant**

   Click **"Create Assistant"** to save the new assistant with all your customizations applied.

4. **Test the assistant**

   After successful creation, click the **"Call Agent"** button to test your new voice assistant immediately.

---

## Important Notes :

- **Retention Period :** Assistants are automatically removed after the selected retention period. This prevents unused demo assistants from accumulating in the system.

- **Template Preservation :** Creating a new assistant does not modify the original template. Your customizations are applied to a copy.

- **Variable Replacement :** All variables you configure are replaced in both the system prompt and the first message when the assistant is created.

- **FAQ Integration :** Generated FAQ prompts are appended to the assistant's system prompt during creation.

- **Explain Due Updates :** Custom Explain Due messages replace the original section in the system prompt when the assistant is created.
