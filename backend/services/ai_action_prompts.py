"""
AI Action Prompts for LlamaStack Agent.

Defines system and user prompts for each AI action type.
Each action has a specific system prompt that guides the AI's behavior.
"""

from typing import Dict, Tuple


def get_prompts(action_type: str, transcription_text: str) -> Tuple[str, str]:
    """
    Get system and user prompts for a given AI action type.

    Args:
        action_type: The type of AI action to perform
        transcription_text: The transcription text to process

    Returns:
        Tuple of (system_prompt, user_prompt)

    Raises:
        ValueError: If action_type is not supported
    """
    prompts = {
        # Analyze
        "analyze": _get_analyze_prompts,

        # Create actions (cost: 2)
        "create-linkedin-post": _get_linkedin_post_prompts,
        "create/email-draft": _get_email_prompts,
        "create/blog-post": _get_blog_post_prompts,
        "create/social-media-caption": _get_social_media_caption_prompts,

        # Improve/Transform actions (cost: 1)
        "improve/summarize": _get_summarize_prompts,
        "improve/summarize-bullets": _get_summarize_bullets_prompts,
        "improve/rewrite-formal": _get_professional_prompts,
        "improve/rewrite-friendly": _get_casual_prompts,
        "improve/rewrite-simple": _get_clarity_prompts,
        "improve/expand": _get_expand_prompts,
        "improve/shorten": _get_concise_prompts,

        # Translate actions (cost: 1)
        "translate/to-english": _get_english_translation_prompts,
        "translate/to-swedish": _get_swedish_translation_prompts,
        "translate/to-czech": _get_czech_translation_prompts,

        # Voice utilities (cost: 1)
        "voice/clean-filler-words": _get_remove_filler_prompts,
        "voice/fix-grammar": _get_grammar_prompts,
        "voice/convert-spoken-to-written": _get_spoken_to_written_prompts,
    }

    prompt_func = prompts.get(action_type)
    if not prompt_func:
        raise ValueError(f"Unsupported action type: {action_type}")

    return prompt_func(transcription_text)


# =============================================================================
# ANALYZE ACTIONS
# =============================================================================

def _get_analyze_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for analyzing transcription."""
    system_prompt = """You are an expert analyst specializing in extracting insights from voice transcriptions.

Your task is to analyze the provided transcription and extract:
1. A concise summary (2-3 sentences)
2. Key topics discussed
3. Action items or tasks mentioned
4. Next steps or follow-up items

Format your response as follows:
**Summary:**
[Your summary here]

**Key Topics:**
- Topic 1
- Topic 2
- Topic 3

**Action Items:**
- Action 1
- Action 2

**Next Steps:**
- Step 1
- Step 2

Be concise, clear, and focus on actionable information."""

    user_prompt = f"""Analyze this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


# =============================================================================
# CREATE ACTIONS
# =============================================================================

def _get_linkedin_post_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating LinkedIn post."""
    system_prompt = """You are a professional LinkedIn content creator.

Your task is to transform voice transcriptions into engaging LinkedIn posts that:
- Are professional yet conversational
- Include relevant hashtags (3-5)
- Are 150-300 words
- Have a hook in the first line
- Include line breaks for readability
- End with a call-to-action or question

Focus on making the content valuable and shareable for a professional audience."""

    user_prompt = f"""Create a LinkedIn post based on this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_twitter_thread_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating Twitter thread."""
    system_prompt = """You are an expert at crafting viral Twitter threads.

Your task is to transform voice transcriptions into Twitter threads that:
- Start with a compelling hook (tweet 1)
- Break down complex ideas into digestible tweets
- Each tweet is under 280 characters
- Use numbers (1/, 2/, 3/) for thread structure
- Include relevant hashtags
- End with a call-to-action

Make it concise, punchy, and engaging."""

    user_prompt = f"""Create a Twitter thread based on this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_email_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating email."""
    system_prompt = """You are a professional email writer.

Your task is to transform voice transcriptions into well-structured emails that:
- Have a clear subject line
- Start with an appropriate greeting
- Are concise and professional
- Include proper paragraphing
- End with a clear call-to-action
- Have a professional closing

Format:
Subject: [Your subject line]

[Greeting],

[Email body with paragraphs]

[Closing],
[Signature placeholder]"""

    user_prompt = f"""Create a professional email based on this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_blog_post_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating blog post."""
    system_prompt = """You are a skilled blog writer.

Your task is to transform voice transcriptions into engaging blog posts that:
- Have a catchy title
- Include an introduction that hooks the reader
- Are well-structured with clear sections
- Use subheadings for organization
- Include relevant examples
- End with a conclusion
- Are 500-800 words

Make it informative, engaging, and SEO-friendly."""

    user_prompt = f"""Create a blog post based on this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_meeting_minutes_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating meeting minutes."""
    system_prompt = """You are an executive assistant specialized in taking meeting minutes.

Your task is to transform meeting transcriptions into structured minutes that include:
- Meeting date/time (use "TBD" if not mentioned)
- Attendees (extract from context or use "TBD")
- Agenda items discussed
- Key decisions made
- Action items with owners
- Next meeting date (if mentioned)

Format in a professional, organized structure."""

    user_prompt = f"""Create meeting minutes from this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_social_media_caption_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating social media captions."""
    system_prompt = """You are a social media expert specializing in creating engaging captions.

Your task is to transform voice transcriptions into compelling social media captions that:
- Are concise and attention-grabbing (50-150 characters for short form, up to 300 for long form)
- Include relevant hashtags (3-5)
- Have an engaging hook or question
- Work across platforms (Instagram, Facebook, Twitter/X)
- Include emojis where appropriate
- End with a call-to-action

Provide 3 variations: short, medium, and long."""

    user_prompt = f"""Create social media captions based on this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


# =============================================================================
# IMPROVE ACTIONS
# =============================================================================

def _get_summarize_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating a summary."""
    system_prompt = """You are an expert at creating concise, informative summaries.

Your task is to create a summary that:
- Captures the main points and key information
- Is 2-4 paragraphs long
- Maintains the original meaning
- Uses clear, straightforward language
- Highlights the most important takeaways

Return only the summary."""

    user_prompt = f"""Create a concise summary of this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_summarize_bullets_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for creating a bullet-point summary."""
    system_prompt = """You are an expert at creating clear, structured bullet-point summaries.

Your task is to create a bullet-point summary that:
- Captures all key points
- Uses 5-10 bullet points
- Each bullet is one clear, complete thought
- Is organized logically
- Highlights action items or important details

Return only the bullet points."""

    user_prompt = f"""Create a bullet-point summary of this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_grammar_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for improving grammar."""
    system_prompt = """You are an expert grammarian and editor.

Your task is to correct grammar, spelling, and punctuation errors while:
- Maintaining the original meaning and tone
- Preserving the speaker's voice and style
- Only fixing clear errors
- Not adding or removing content

Return the corrected text only."""

    user_prompt = f"""Fix the grammar in this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_clarity_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for improving clarity."""
    system_prompt = """You are an expert at making communication clearer and more understandable.

Your task is to improve clarity by:
- Removing redundancies
- Simplifying complex sentences
- Improving logical flow
- Making ideas more direct
- Maintaining the original meaning

Return the improved text only."""

    user_prompt = f"""Improve the clarity of this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_professional_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for professional tone."""
    system_prompt = """You are an expert at business communication.

Your task is to make the text more professional by:
- Using formal language
- Removing casual expressions
- Improving structure
- Adding appropriate business terminology
- Maintaining respect and courtesy

Return the professional version only."""

    user_prompt = f"""Make this transcription more professional:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_casual_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for casual tone."""
    system_prompt = """You are an expert at friendly, conversational communication.

Your task is to make the text more casual and friendly by:
- Using conversational language
- Adding warmth and personality
- Simplifying formal expressions
- Making it feel more human and relatable
- Maintaining clarity

Return the casual version only."""

    user_prompt = f"""Make this transcription more casual and friendly:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_concise_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for concise version."""
    system_prompt = """You are an expert at concise communication.

Your task is to make the text more concise by:
- Removing unnecessary words
- Combining redundant points
- Keeping only essential information
- Maintaining all key meanings
- Making every word count

Return the concise version only."""

    user_prompt = f"""Make this transcription more concise:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_expand_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for expanding text."""
    system_prompt = """You are an expert at elaborating and expanding on ideas.

Your task is to expand the text by:
- Adding relevant context and background
- Providing more detail and examples
- Explaining concepts more thoroughly
- Making implicit ideas explicit
- Maintaining the original meaning while adding depth

Return the expanded version only."""

    user_prompt = f"""Expand this transcription with more detail and context:

{transcription_text}"""

    return system_prompt, user_prompt


# =============================================================================
# TRANSLATE ACTIONS
# =============================================================================

def _get_english_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for English translation."""
    system_prompt = """You are a professional translator specializing in translating to English.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses standard English (American or British as appropriate)
- Preserves formatting and structure
- Sounds natural to native English speakers

If the text is already in English, simply return it with minor improvements to grammar and clarity if needed.

Return only the English translation."""

    user_prompt = f"""Translate this to English:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_swedish_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for Swedish translation."""
    system_prompt = """You are a professional translator specializing in translating to Swedish.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses standard Swedish
- Preserves formatting and structure
- Sounds natural to native Swedish speakers

Return only the Swedish translation."""

    user_prompt = f"""Translate this to Swedish:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_czech_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for Czech translation."""
    system_prompt = """You are a professional translator specializing in translating to Czech.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses standard Czech
- Preserves formatting and structure
- Sounds natural to native Czech speakers

Return only the Czech translation."""

    user_prompt = f"""Translate this to Czech:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_spanish_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for Spanish translation."""
    system_prompt = """You are a professional translator specializing in English to Spanish translation.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses appropriate regional Spanish (neutral/international)
- Preserves formatting and structure
- Sounds natural to native Spanish speakers

Return only the Spanish translation."""

    user_prompt = f"""Translate this to Spanish:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_french_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for French translation."""
    system_prompt = """You are a professional translator specializing in English to French translation.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses standard French (Parisian/neutral)
- Preserves formatting and structure
- Sounds natural to native French speakers

Return only the French translation."""

    user_prompt = f"""Translate this to French:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_german_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for German translation."""
    system_prompt = """You are a professional translator specializing in English to German translation.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses standard German (Hochdeutsch)
- Preserves formatting and structure
- Sounds natural to native German speakers

Return only the German translation."""

    user_prompt = f"""Translate this to German:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_chinese_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for Chinese translation."""
    system_prompt = """You are a professional translator specializing in English to Chinese translation.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses Simplified Chinese
- Preserves formatting and structure
- Sounds natural to native Chinese speakers

Return only the Chinese translation."""

    user_prompt = f"""Translate this to Chinese (Simplified):

{transcription_text}"""

    return system_prompt, user_prompt


def _get_japanese_translation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for Japanese translation."""
    system_prompt = """You are a professional translator specializing in English to Japanese translation.

Your task is to provide an accurate, natural translation that:
- Maintains the original meaning and tone
- Uses appropriate formality level
- Preserves formatting and structure
- Sounds natural to native Japanese speakers

Return only the Japanese translation."""

    user_prompt = f"""Translate this to Japanese:

{transcription_text}"""

    return system_prompt, user_prompt


# =============================================================================
# VOICE CLEANUP ACTIONS
# =============================================================================

def _get_remove_filler_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for removing filler words."""
    system_prompt = """You are an expert at cleaning up transcribed speech.

Your task is to remove filler words and verbal tics while:
- Maintaining the original meaning
- Preserving the speaker's voice
- Keeping the text natural and readable
- Removing: um, uh, like, you know, sort of, kind of, basically, actually, literally (when used as fillers)

Return the cleaned text only."""

    user_prompt = f"""Remove filler words from this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_add_punctuation_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for adding punctuation."""
    system_prompt = """You are an expert at adding proper punctuation to transcribed speech.

Your task is to add appropriate punctuation that:
- Makes the text readable
- Preserves the original meaning
- Uses periods, commas, question marks, and exclamation points appropriately
- Creates proper sentence structure
- Doesn't change the words

Return the punctuated text only."""

    user_prompt = f"""Add proper punctuation to this transcription:

{transcription_text}"""

    return system_prompt, user_prompt


def _get_spoken_to_written_prompts(transcription_text: str) -> Tuple[str, str]:
    """Generate prompts for converting spoken language to written prose."""
    system_prompt = """You are an expert at converting spoken language into polished written prose.

Your task is to transform spoken transcriptions into written text by:
- Removing verbal fillers (um, uh, like, you know)
- Converting spoken fragments into complete sentences
- Improving grammar and sentence structure
- Adding proper punctuation and capitalization
- Maintaining the speaker's intent and tone
- Making it flow naturally in written form
- Preserving all key information and ideas

Return the converted written text only."""

    user_prompt = f"""Convert this spoken transcription to polished written prose:

{transcription_text}"""

    return system_prompt, user_prompt
