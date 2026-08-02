// Sample data for the free demo (no backend). Patient: "Eleanor" (patient_123).

export const TOPICS = [
  'daily_routine',
  'family_history',
  'hobbies',
  'health_info',
  'preferences',
  'positive_memory',
  'career',
]

export const EMOTIONS = ['positive', 'negative', 'neutral', 'mixed']

export const SOURCES = [
  'family_questionnaire',
  'family_interview',
  'caregiver_input',
  'patient_conversation',
  'medical_record',
]

const mem = (i, text, topic, emotion, source, entities, is_sensitive = false, daysAgo = i) => ({
  uuid: `demo-mem-${String(i).padStart(3, '0')}`,
  patient_id: 'patient_123',
  text,
  topic,
  emotion,
  source,
  entities,
  is_sensitive,
  chunk_index: 0,
  total_chunks: 1,
  ingested_at: new Date(Date.now() - daysAgo * 86400000).toISOString(),
})

export const SAMPLE_MEMORIES = [
  mem(
    1,
    'Eleanor wakes around 7am each morning, makes a cup of Earl Grey tea, and does gentle stretches by the window while watching the birds in her garden.',
    'daily_routine',
    'positive',
    'family_questionnaire',
    ['Earl Grey tea', 'garden', 'birds']
  ),
  mem(
    2,
    "Her son Robert visits every Sunday afternoon. They usually have lunch together and he helps with anything around the house that she can't easily manage.",
    'family_history',
    'positive',
    'family_interview',
    ['Robert', 'Sunday']
  ),
  mem(
    3,
    'Eleanor was married to George for 51 years. He passed away three years ago. She keeps a photo of the two of them from their trip to the coast on her nightstand.',
    'family_history',
    'mixed',
    'patient_conversation',
    ['George', 'coast']
  ),
  mem(
    4,
    'She adores gardening, especially her roses. Last week she was overjoyed when the first buds of the season bloomed by the front step.',
    'hobbies',
    'positive',
    'caregiver_input',
    ['roses', 'garden']
  ),
  mem(
    5,
    'Eleanor takes a blood-pressure tablet every morning with breakfast. She sometimes forgets, so a gentle reminder around 8am is helpful.',
    'health_info',
    'neutral',
    'medical_record',
    ['blood pressure', 'breakfast'],
    true
  ),
  mem(
    6,
    'She has mild arthritis in her hands, which makes opening jars and bottles difficult. Easy-grip tools have made a real difference for her.',
    'health_info',
    'mixed',
    'medical_record',
    ['arthritis', 'hands'],
    true
  ),
  mem(
    7,
    'Eleanor loves old black-and-white films, particularly musicals. She can recite lines from her favourites and hums the songs while cooking.',
    'hobbies',
    'positive',
    'patient_conversation',
    ['films', 'musicals']
  ),
  mem(
    8,
    'She worked as a primary school teacher for over thirty years and still lights up when former students recognise her in town.',
    'career',
    'positive',
    'family_interview',
    ['teacher', 'students']
  ),
  mem(
    9,
    'Eleanor enjoys classical music, especially in the evenings. She strongly dislikes loud, sudden noises, which can startle her.',
    'preferences',
    'neutral',
    'family_questionnaire',
    ['classical music']
  ),
  mem(
    10,
    'Her grandchildren, Mia and Liam, call on video chat most Wednesdays. She looks forward to it all week and loves hearing about school.',
    'family_history',
    'positive',
    'family_interview',
    ['Mia', 'Liam', 'Wednesday']
  ),
  mem(
    11,
    'She felt lonely and a little low during the long rainy spell last month, when she could not get out into the garden as usual.',
    'positive_memory',
    'negative',
    'patient_conversation',
    ['garden', 'rain']
  ),
  mem(
    12,
    'Eleanor does the newspaper crossword every day with her afternoon tea and is quietly proud that she rarely needs help finishing it.',
    'hobbies',
    'positive',
    'caregiver_input',
    ['crossword', 'tea']
  ),
]

// Canned hazard-detection result so the Hazard Detector page shows a realistic output for free.
export const SAMPLE_HAZARD_RESULT = {
  success: true,
  message:
    'Hazard detection completed (demo) — analysed a hallway scene, found 2 potential hazards.',
  output:
    'DEMO MODE: This is a pre-recorded sample analysis. In the full app, frames are sent to ' +
    'Gemini Vision for live hazard detection.',
  images: [
    {
      image_filename: 'hallway_demo.jpg',
      image_url: '/senior-assistant-banner.png',
      result: {
        people_detected: false,
        hazard_detected: true,
        hazards: [
          {
            type: 'Loose rug',
            severity: 'high',
            location: 'Center of hallway',
            details: 'Rug edge is curled and not secured — a trip hazard along the main walkway.',
          },
          {
            type: 'Low lighting',
            severity: 'medium',
            location: 'Far end of hallway',
            details: 'Dim lighting reduces visibility of obstacles near the doorway.',
          },
        ],
        summary:
          'Two hazards identified along the walkway. Securing the rug and improving lighting ' +
          'would reduce fall risk.',
      },
    },
  ],
}
