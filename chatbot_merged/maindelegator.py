from convo import Conversation
import dotenv

class delegation:
    @staticmethod
    async def delegate(command):
        dotenv.load_dotenv("keys.env")

        PERSONA1 = """
        John Doe, an 86-year-old man, manages several chronic health conditions: diabetes, high blood pressure, and high cholesterol. His diabetes is controlled with Metformin, prescribed to enhance insulin sensitivity and help regulate blood sugar levels. He takes 1000 mg twice daily, which is essential for managing his type 2 diabetes. Additionally, he utilizes a continuous glucose monitor to track his blood sugar throughout the day, allowing for timely adjustments in his diet or medication.

        For hypertension, Mr. Thompson is on Lisinopril, an ACE inhibitor that helps relax blood vessels and lower blood pressure. He takes a daily dose of 10 mg. Regular monitoring of his blood pressure is essential, and his target is consistently maintained around 120/80 mmHg. To manage his cholesterol levels, he takes Atorvastatin, a statin medication that lowers LDL cholesterol and raises HDL cholesterol. His regimen includes 20 mg daily, which has successfully maintained his cholesterol levels within a healthy range.

        Mr. Thompson also adheres to a heart-healthy diet low in saturated fats and sugars, complemented with regular exercise, which his doctor has endorsed. He is encouraged to stay hydrated and manage his carbohydrate intake carefully due to his diabetes. To prevent any potential complications, he receives regular lab tests to monitor kidney function and overall metabolic health. Additionally, he takes a daily Aspirin regimen for cardiovascular protection, in consultation with his healthcare provider. Following this comprehensive medication and lifestyle management, Mr. Thompson effectively maintains his health and quality of life.
        """

        PERSONA2 = """
        Jane Doe, an 81-year-old woman with stage 2 lung cancer, kidney stones, and epilepsy follows a comprehensive medication regimen tailored to her complex medical needs. For her lung cancer, she is receiving chemotherapy, specifically a combination of cisplatin and pemetrexed, aimed at controlling tumor growth and alleviating symptoms. She takes these medications every three weeks, with anti-nausea medications like ondansetron to manage potential side effects.

        To address her kidney stones, the woman is prescribed an alpha-blocker, tamsulosin, to facilitate the passage of stones and alleviate any associated discomfort. She also takes potassium citrate to help dissolve certain types of stones and decrease the likelihood of new stone formation. Adequate hydration is critical, so she consciously increases her fluid intake, often aiming for at least 2 liters of water daily.

        Her epilepsy is controlled through the use of levetiracetam, an anticonvulsant that helps minimize seizure frequency and severity. She monitors her medication adherence carefully, taking levetiracetam twice daily as directed, while being aware of any potential interactions with her cancer and kidney medications.

        To support her overall health, she may also be prescribed a multivitamin to help mitigate nutritional deficiencies that can arise from concurrent treatments. Regular follow-up visits with her healthcare team ensure her medications are adjusted as needed, particularly in response to treatment tolerability and evolving health conditions. This comprehensive plan not only addresses her primary health issues but also aims to improve her quality of life in her senior years.
        """

        print("we're delegating")

        conversation = Conversation(personas=[PERSONA1, PERSONA2])

        result = conversation.stream_reply(command)
        #print(result)
        # To get the full output as one string:
        response = "Response "
        #for token in result:
        #   print(token, end="", flush=True)

        for chunk in result:
            #print(chunk)
            response += chunk

        print(response)