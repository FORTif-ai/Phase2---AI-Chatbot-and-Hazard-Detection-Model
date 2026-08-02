// Offline demo replies for static hosting (e.g. GitHub Pages), where no serverless
// function is available. Simple keyword matching over Eleanor's sample memories so the
// chat feels intentional and on-topic rather than erroring.

const RULES = [
  {
    match: /(hello|hi|hey|good (morning|afternoon|evening)|how are you)/,
    reply:
      "Hello! I'm Fortif.ai, Eleanor's companion. I can tell you about her family, her daily " +
      'routine, her garden, or her hobbies — what would you like to know?',
  },
  {
    match: /(family|son|robert|husband|george|grandchild|grandkid|mia|liam|visit)/,
    reply:
      'Eleanor is close with her family. Her son Robert visits every Sunday for lunch, and her ' +
      'grandchildren Mia and Liam video-call most Wednesdays. She was married to George for 51 ' +
      'wonderful years.',
  },
  {
    match: /(morning|routine|wake|tea|breakfast|day)/,
    reply:
      'Eleanor usually wakes around 7am, makes a cup of Earl Grey tea, and does gentle stretches ' +
      'by the window while watching the birds. A little reminder for her morning tablet around ' +
      '8am is always appreciated.',
  },
  {
    match: /(garden|rose|flower|plant|outside)/,
    reply:
      'Gardening is one of Eleanor’s greatest joys — especially her roses. She was ' +
      'overjoyed last week when the first buds of the season bloomed by her front step.',
  },
  {
    match: /(medic|medication|pill|tablet|blood pressure|health|arthritis|doctor)/,
    reply:
      'Eleanor takes a blood-pressure tablet each morning with breakfast, and her arthritis can ' +
      'make jars tricky, so easy-grip tools help. For anything medical, it’s best to check ' +
      'with her caregiver or doctor — I’m here for gentle reminders and company.',
  },
  {
    match: /(hobby|hobbies|film|movie|music|crossword|fun|enjoy|like)/,
    reply:
      'Eleanor loves old black-and-white musicals (she hums the songs while cooking!), the daily ' +
      'crossword with her afternoon tea, and classical music in the evenings.',
  },
  {
    match: /(work|career|job|teacher|school|students)/,
    reply:
      'Eleanor was a primary school teacher for over thirty years. She still lights up whenever a ' +
      'former student recognises her around town.',
  },
  {
    match: /(lonely|sad|down|low|rain|bored|miss)/,
    reply:
      "I'm sorry you're feeling that way, Eleanor. Rainy spells away from the garden can feel " +
      'long. Would some classical music or a call with Mia and Liam lift your spirits a little?',
  },
]

export function demoReply(question) {
  const q = (question || '').toLowerCase()
  const hit = RULES.find((r) => r.match.test(q))
  if (hit) return hit.reply
  return (
    "That's a lovely question. I know Eleanor well — her family, her morning routine, her " +
    'garden, her hobbies, and her health reminders. Ask me about any of those and I’ll share ' +
    'what I know!'
  )
}
