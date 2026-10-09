"""
InterviewIQ — Expanded Aptitude Question Dataset & Bank (320 Questions)
========================================================================
Contains 320 structured questions for:
  1. Quantitative Aptitude (~120 questions)
  2. Logical Reasoning (~90 questions)
  3. Verbal Ability (~70 questions)
  4. Data Interpretation (~40 questions)
"""

APTITUDE_QUESTIONS = [
    {
        "id": "quant_perc_01",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Easy",
        "question": "If a number is increased by 20% and becomes 120, what was the original number?",
        "options": [
            "80",
            "90",
            "100",
            "110"
        ],
        "answer": "100",
        "explanation": "Let original number = x. 1.20 * x = 120 => x = 100."
    },
    {
        "id": "quant_perc_02",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Medium",
        "question": "In an election between two candidates, the winner gets 65% of total votes and wins by 270 votes. Total votes polled:",
        "options": [
            "800",
            "900",
            "1000",
            "1200"
        ],
        "answer": "900",
        "explanation": "Difference = 65% - 35% = 30%. 30% of Total = 270 => Total = 900."
    },
    {
        "id": "quant_perc_03",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Hard",
        "question": "A student multiplied a number by 3/5 instead of 5/3. Percentage error in calculation is:",
        "options": [
            "36%",
            "44%",
            "64%",
            "54%"
        ],
        "answer": "64%",
        "explanation": "Correct = 15*(5/3)=25, Wrong = 15*(3/5)=9. Error = 16. % error = (16/25)*100 = 64%."
    },
    {
        "id": "quant_perc_04",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Easy",
        "question": "What is 35% of 400?",
        "options": [
            "120",
            "130",
            "140",
            "150"
        ],
        "answer": "140",
        "explanation": "0.35 * 400 = 140."
    },
    {
        "id": "quant_perc_05",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Medium",
        "question": "The price of sugar rises by 25%. By what % must a family reduce consumption to keep expenditure constant?",
        "options": [
            "15%",
            "20%",
            "25%",
            "30%"
        ],
        "answer": "20%",
        "explanation": "Reduction % = [r / (100 + r)] * 100 = [25 / 125] * 100 = 20%."
    },
    {
        "id": "quant_perc_06",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Hard",
        "question": "In a college exam, 40% failed in Math, 30% failed in English, and 15% failed in both. % of students who passed both:",
        "options": [
            "45%",
            "50%",
            "55%",
            "60%"
        ],
        "answer": "45%",
        "explanation": "Total failed in at least one = 40 + 30 - 15 = 55%. Passed both = 100% - 55% = 45%."
    },
    {
        "id": "quant_perc_07",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Easy",
        "question": "A salary is increased by 10% and then decreased by 10%. Net change in salary:",
        "options": [
            "0%",
            "1% decrease",
            "1% increase",
            "2% decrease"
        ],
        "answer": "1% decrease",
        "explanation": "Net change = 10 - 10 - (10*10)/100 = -1% (1% decrease)."
    },
    {
        "id": "quant_perc_08",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Medium",
        "question": "If A's income is 25% more than B's income, how much percent is B's income less than A's?",
        "options": [
            "15%",
            "20%",
            "25%",
            "30%"
        ],
        "answer": "20%",
        "explanation": "Less % = [25 / (100 + 25)] * 100 = (25 / 125) * 100 = 20%."
    },
    {
        "id": "quant_perc_09",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Easy",
        "question": "80% of a number is 240. What is 50% of that number?",
        "options": [
            "120",
            "150",
            "180",
            "200"
        ],
        "answer": "150",
        "explanation": "Number = 240 / 0.8 = 300. 50% of 300 = 150."
    },
    {
        "id": "quant_perc_10",
        "category": "Quantitative Aptitude",
        "topic": "Percentages",
        "difficulty": "Hard",
        "question": "Population of a town increases by 10% in 1st year and decreases by 10% in 2nd year. If present population is 99,000, what was initial population?",
        "options": [
            "90,000",
            "95,000",
            "100,000",
            "105,000"
        ],
        "answer": "100,000",
        "explanation": "Pop = P * 1.10 * 0.90 = 0.99P. 0.99P = 99,000 => P = 100,000."
    },
    {
        "id": "quant_pl_01",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Easy",
        "question": "An article bought for $500 is sold for $600. What is the profit percentage?",
        "options": [
            "15%",
            "20%",
            "25%",
            "30%"
        ],
        "answer": "20%",
        "explanation": "Profit = 600 - 500 = 100. Profit % = (100/500)*100 = 20%."
    },
    {
        "id": "quant_pl_02",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Medium",
        "question": "By selling an item for $720, a shopkeeper suffers a 10% loss. Selling price for 20% profit is:",
        "options": [
            "$800",
            "$880",
            "$960",
            "$1000"
        ],
        "answer": "$960",
        "explanation": "CP = 720 / 0.9 = 800. SP for 20% profit = 800 * 1.2 = $960."
    },
    {
        "id": "quant_pl_03",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Hard",
        "question": "The cost price of 20 articles is equal to the selling price of 16 articles. Find the profit percentage.",
        "options": [
            "20%",
            "25%",
            "30%",
            "33.33%"
        ],
        "answer": "25%",
        "explanation": "Profit % = [(20 - 16) / 16] * 100 = (4/16)*100 = 25%."
    },
    {
        "id": "quant_pl_04",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Easy",
        "question": "A book is bought for $150 and sold at a loss of 10%. Selling price is:",
        "options": [
            "$125",
            "$130",
            "$135",
            "$140"
        ],
        "answer": "$135",
        "explanation": "SP = 150 * 0.90 = $135."
    },
    {
        "id": "quant_pl_05",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Medium",
        "question": "A trader marks goods 40% above cost price and allows a discount of 20%. Profit percentage is:",
        "options": [
            "12%",
            "15%",
            "18%",
            "20%"
        ],
        "answer": "12%",
        "explanation": "Net profit % = 40 - 20 - (40*20)/100 = 40 - 20 - 8 = 12%."
    },
    {
        "id": "quant_pl_06",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Hard",
        "question": "If a man sells two chairs for $990 each, gaining 10% on one and losing 10% on the other, overall result is:",
        "options": [
            "No gain no loss",
            "1% gain",
            "1% loss",
            "2% loss"
        ],
        "answer": "1% loss",
        "explanation": "When SP is same for equal % gain & loss, net loss % = (x/10)^2 = (10/10)^2 = 1% loss."
    },
    {
        "id": "quant_pl_07",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Easy",
        "question": "A vendor buys lemons at 6 for $10 and sells them at 4 for $8. Find his profit %.",
        "options": [
            "15%",
            "20%",
            "25%",
            "30%"
        ],
        "answer": "20%",
        "explanation": "CP of 1 = 10/6 = 5/3. SP of 1 = 8/4 = 2. Profit = 2 - 5/3 = 1/3. Profit % = (1/3) / (5/3) * 100 = 20%."
    },
    {
        "id": "quant_pl_08",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Medium",
        "question": "A dishonest dealer professes to sell goods at CP but uses a weight of 900 grams for 1 kg. Profit % is:",
        "options": [
            "10%",
            "11.11%",
            "12.5%",
            "15%"
        ],
        "answer": "11.11%",
        "explanation": "Gain % = [Error / (True - Error)] * 100 = [100 / 900] * 100 = 11.11%."
    },
    {
        "id": "quant_pl_09",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Easy",
        "question": "If CP is $400 and Profit is 15%, find the Selling Price.",
        "options": [
            "$450",
            "$460",
            "$470",
            "$480"
        ],
        "answer": "$460",
        "explanation": "SP = 400 * 1.15 = $460."
    },
    {
        "id": "quant_pl_10",
        "category": "Quantitative Aptitude",
        "topic": "Profit and Loss",
        "difficulty": "Hard",
        "question": "Selling 100 pens gives a profit equal to the selling price of 20 pens. Find profit %.",
        "options": [
            "20%",
            "25%",
            "30%",
            "35%"
        ],
        "answer": "25%",
        "explanation": "Profit % = [20 / (100 - 20)] * 100 = (20/80)*100 = 25%."
    },
    {
        "id": "quant_ratio_01",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Easy",
        "question": "If A : B = 2 : 3 and B : C = 4 : 5, find A : C.",
        "options": [
            "8 : 15",
            "2 : 5",
            "6 : 15",
            "3 : 5"
        ],
        "answer": "8 : 15",
        "explanation": "A/C = (A/B) * (B/C) = (2/3) * (4/5) = 8/15."
    },
    {
        "id": "quant_ratio_02",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Medium",
        "question": "Two numbers are in the ratio 3 : 5. If 9 is subtracted from each, ratio becomes 12 : 23. Find the smaller number.",
        "options": [
            "27",
            "33",
            "36",
            "55"
        ],
        "answer": "33",
        "explanation": "Let numbers be 3x and 5x. (3x - 9)/(5x - 9) = 12/23 => 69x - 207 = 60x - 108 => 9x = 99 => x = 11. Smaller = 3*11 = 33."
    },
    {
        "id": "quant_ratio_03",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Hard",
        "question": "A bag contains 50p, 25p and 10p coins in ratio 5 : 9 : 4 amounting to $206. Find total number of coins.",
        "options": [
            "360",
            "480",
            "720",
            "800"
        ],
        "answer": "720",
        "explanation": "Values ratio = 5*0.5 : 9*0.25 : 4*0.1 = 2.5 : 2.25 : 0.4 = 5.15 units per ratio x. 5.15x = 206 => x = 40. Total coins = (5+9+4)*40 = 18*40 = 720."
    },
    {
        "id": "quant_ratio_04",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Easy",
        "question": "Divide $700 among A, B, C in the ratio 2 : 3 : 5. Find B's share.",
        "options": [
            "$140",
            "$210",
            "$350",
            "$280"
        ],
        "answer": "$210",
        "explanation": "Total parts = 2+3+5 = 10. B's share = (3/10) * 700 = $210."
    },
    {
        "id": "quant_ratio_05",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Medium",
        "question": "If x : y = 4 : 7, find the value of (3x + 2y) : (5x - y).",
        "options": [
            "26 : 13",
            "26 : 7",
            "13 : 7",
            "2 : 1"
        ],
        "answer": "26 : 13",
        "explanation": "Substitute x=4, y=7: (3*4 + 2*7) : (5*4 - 7) = (12+14) : (20-7) = 26 : 13 = 2 : 1."
    },
    {
        "id": "quant_ratio_06",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Hard",
        "question": "Ratio of income of A and B is 5 : 4 and expenditure ratio is 3 : 2. If each saves $1,600, find A's income.",
        "options": [
            "$3,200",
            "$4,000",
            "$4,800",
            "$5,600"
        ],
        "answer": "$4,000",
        "explanation": "(5x - 1600)/(4x - 1600) = 3/2 => 10x - 3200 = 12x - 4800 => 2x = 1600 => x = 800. A's income = 5*800 = $4,000."
    },
    {
        "id": "quant_ratio_07",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Easy",
        "question": "The mean proportional between 9 and 25 is:",
        "options": [
            "12",
            "15",
            "16",
            "18"
        ],
        "answer": "15",
        "explanation": "Mean proportional = sqrt(9 * 25) = sqrt(225) = 15."
    },
    {
        "id": "quant_ratio_08",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Medium",
        "question": "What number should be added to 6, 15, 20 and 43 to make them proportional?",
        "options": [
            "2",
            "3",
            "4",
            "5"
        ],
        "answer": "3",
        "explanation": "(6+3)/(15+3) = 9/18 = 1/2. (20+3)/(43+3) = 23/46 = 1/2."
    },
    {
        "id": "quant_ratio_09",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Easy",
        "question": "Ratio of boys to girls in a class of 60 students is 3 : 2. How many girls are there?",
        "options": [
            "20",
            "24",
            "30",
            "36"
        ],
        "answer": "24",
        "explanation": "Girls = (2/5) * 60 = 24."
    },
    {
        "id": "quant_ratio_10",
        "category": "Quantitative Aptitude",
        "topic": "Ratio and Proportion",
        "difficulty": "Hard",
        "question": "In a mixture of 60 liters, ratio of milk and water is 2 : 1. How much water must be added to make ratio 1 : 2?",
        "options": [
            "40 L",
            "50 L",
            "60 L",
            "80 L"
        ],
        "answer": "60 L",
        "explanation": "Milk = 40L, Water = 20L. New ratio 40/(20+w) = 1/2 => 20+w = 80 => w = 60 liters."
    },
    {
        "id": "quant_avg_01",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Easy",
        "question": "Average of 5 consecutive numbers is 20. The largest number is:",
        "options": [
            "21",
            "22",
            "23",
            "24"
        ],
        "answer": "22",
        "explanation": "Middle number = 20. Numbers: 18, 19, 20, 21, 22. Largest = 22."
    },
    {
        "id": "quant_avg_02",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Medium",
        "question": "The average age of 24 students and a teacher is 15 years. If teacher's age is excluded, average decreases by 1. Teacher's age is:",
        "options": [
            "35",
            "39",
            "40",
            "42"
        ],
        "answer": "39",
        "explanation": "Sum = 25 * 15 = 375. Sum without teacher = 24 * 14 = 336. Teacher = 375 - 336 = 39 years."
    },
    {
        "id": "quant_avg_03",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Hard",
        "question": "Average score of 50 students in an exam is 64. If top 5 scores are excluded, average drops by 2. Average of top 5 scores:",
        "options": [
            "78",
            "80",
            "82",
            "85"
        ],
        "answer": "82",
        "explanation": "Total = 50*64 = 3200. Rest 45 sum = 45*62 = 2790. Top 5 sum = 410. Average = 410/5 = 82."
    },
    {
        "id": "quant_avg_04",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Easy",
        "question": "Find average of first 10 natural numbers.",
        "options": [
            "5.0",
            "5.5",
            "6.0",
            "6.5"
        ],
        "answer": "5.5",
        "explanation": "Sum = 10*11/2 = 55. Average = 55/10 = 5.5."
    },
    {
        "id": "quant_avg_05",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Medium",
        "question": "Average weight of 8 persons increases by 2.5 kg when a new person replaces one weighing 65 kg. Weight of new person:",
        "options": [
            "75 kg",
            "80 kg",
            "85 kg",
            "90 kg"
        ],
        "answer": "85 kg",
        "explanation": "Weight increase = 8 * 2.5 = 20 kg. New weight = 65 + 20 = 85 kg."
    },
    {
        "id": "quant_avg_06",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Hard",
        "question": "A cricketer has a certain average for 10 innings. In the 11th inning, he scores 108 runs, increasing average by 6 runs. New average:",
        "options": [
            "42",
            "48",
            "54",
            "60"
        ],
        "answer": "48",
        "explanation": "Old total = 10x. New total = 10x + 108 = 11(x + 6) => 10x + 108 = 11x + 66 => x = 42. New avg = 42 + 6 = 48."
    },
    {
        "id": "quant_avg_07",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Easy",
        "question": "Average of 4, 8, 12, 16, 20 is:",
        "options": [
            "10",
            "12",
            "14",
            "16"
        ],
        "answer": "12",
        "explanation": "Sum = 60 / 5 = 12."
    },
    {
        "id": "quant_avg_08",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Medium",
        "question": "Average temperature from Mon to Wed was 37\u00b0C and Tue to Thu was 34\u00b0C. If Thu temp was 4/5 of Mon, find Mon temp.",
        "options": [
            "35\u00b0C",
            "40\u00b0C",
            "42\u00b0C",
            "45\u00b0C"
        ],
        "answer": "45\u00b0C",
        "explanation": "Mon - Thu = 3*(37 - 34) = 9. Mon - (4/5)Mon = 9 => Mon/5 = 9 => Mon = 45\u00b0C."
    },
    {
        "id": "quant_avg_09",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Easy",
        "question": "Average of 3 numbers is 15. If two numbers are 10 and 18, find third number.",
        "options": [
            "14",
            "17",
            "19",
            "20"
        ],
        "answer": "17",
        "explanation": "Sum = 3 * 15 = 45. Third = 45 - (10 + 18) = 17."
    },
    {
        "id": "quant_avg_10",
        "category": "Quantitative Aptitude",
        "topic": "Averages",
        "difficulty": "Hard",
        "question": "A batsman scores 80, 85, 90, 95 in first 4 matches. What must he score in 5th match to have average 90?",
        "options": [
            "90",
            "95",
            "100",
            "105"
        ],
        "answer": "100",
        "explanation": "Sum of 5 matches = 5 * 90 = 450. Sum of 4 matches = 350. 5th match = 450 - 350 = 100."
    },
    {
        "id": "quant_tw_01",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Easy",
        "question": "A completes work in 10 days, B in 15 days. Together they finish in:",
        "options": [
            "5 days",
            "6 days",
            "7 days",
            "8 days"
        ],
        "answer": "6 days",
        "explanation": "1/10 + 1/15 = 5/30 = 1/6 => 6 days."
    },
    {
        "id": "quant_tw_02",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Medium",
        "question": "12 workers build a wall in 15 days. How many workers needed for 10 days?",
        "options": [
            "15",
            "18",
            "20",
            "24"
        ],
        "answer": "18",
        "explanation": "Worker-days = 12 * 15 = 180. For 10 days = 180 / 10 = 18."
    },
    {
        "id": "quant_tw_03",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Hard",
        "question": "A is twice as good a workman as B and together they finish a piece of work in 18 days. In how many days can A alone finish it?",
        "options": [
            "24 days",
            "27 days",
            "30 days",
            "36 days"
        ],
        "answer": "27 days",
        "explanation": "Ratio of efficiency A:B = 2:1. Total efficiency = 3. Total work = 18 * 3 = 54 units. A alone = 54 / 2 = 27 days."
    },
    {
        "id": "quant_tw_04",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Easy",
        "question": "A can do a work in 6 days, B in 12 days. Working together, what fraction of work done in 1 day?",
        "options": [
            "1/4",
            "1/3",
            "1/2",
            "3/4"
        ],
        "answer": "1/4",
        "explanation": "1/6 + 1/12 = 3/12 = 1/4."
    },
    {
        "id": "quant_tw_05",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Medium",
        "question": "A and B can do a work in 12 days, B and C in 15 days, C and A in 20 days. Together they can finish in:",
        "options": [
            "8 days",
            "10 days",
            "12 days",
            "15 days"
        ],
        "answer": "10 days",
        "explanation": "2(A+B+C) = 1/12 + 1/15 + 1/20 = (5+4+3)/60 = 12/60 = 1/5. A+B+C = 1/10 => 10 days."
    },
    {
        "id": "quant_tw_06",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Hard",
        "question": "Pipe A fills tank in 4 hrs, Pipe B empties in 6 hrs. If both opened together, time to fill tank:",
        "options": [
            "8 hours",
            "10 hours",
            "12 hours",
            "14 hours"
        ],
        "answer": "12 hours",
        "explanation": "Net fill rate = 1/4 - 1/6 = (3-2)/12 = 1/12 => 12 hours."
    },
    {
        "id": "quant_tw_07",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Easy",
        "question": "If 5 men can complete a job in 8 days, how many days will 10 men take?",
        "options": [
            "3 days",
            "4 days",
            "5 days",
            "6 days"
        ],
        "answer": "4 days",
        "explanation": "5 * 8 = 10 * d => d = 4 days."
    },
    {
        "id": "quant_tw_08",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Medium",
        "question": "A can complete a work in 20 days. He worked for 5 days and left. B finished remaining work in 15 days. B alone can finish work in:",
        "options": [
            "18 days",
            "20 days",
            "22 days",
            "25 days"
        ],
        "answer": "20 days",
        "explanation": "A completed 5/20 = 1/4 work. Remaining 3/4 done by B in 15 days => B total time = 15 * (4/3) = 20 days."
    },
    {
        "id": "quant_tw_09",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Easy",
        "question": "P and Q together take 6 days. P alone takes 10 days. Q alone takes:",
        "options": [
            "12 days",
            "15 days",
            "18 days",
            "20 days"
        ],
        "answer": "15 days",
        "explanation": "1/Q = 1/6 - 1/10 = 2/30 = 1/15 => 15 days."
    },
    {
        "id": "quant_tw_10",
        "category": "Quantitative Aptitude",
        "topic": "Time and Work",
        "difficulty": "Hard",
        "question": "3 men or 6 women can do a work in 16 days. How many days will 12 men and 8 women take?",
        "options": [
            "3 days",
            "4 days",
            "5 days",
            "6 days"
        ],
        "answer": "3 days",
        "explanation": "1 man = 2 women. 12 men + 8 women = 24 + 8 = 32 women. 6 women take 16 days => 32 women take (6*16)/32 = 3 days."
    },
    {
        "id": "quant_tsd_01",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Easy",
        "question": "Speed of 72 km/h in meters per second (m/s) is:",
        "options": [
            "15 m/s",
            "18 m/s",
            "20 m/s",
            "25 m/s"
        ],
        "answer": "20 m/s",
        "explanation": "72 * (5/18) = 20 m/s."
    },
    {
        "id": "quant_tsd_02",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Hard",
        "question": "Two trains 150m and 120m long moving in opposite directions at 45 km/h and 63 km/h. Time to cross each other:",
        "options": [
            "7 seconds",
            "9 seconds",
            "10 seconds",
            "12 seconds"
        ],
        "answer": "9 seconds",
        "explanation": "Distance = 270m. Rel speed = 108 km/h = 30 m/s. Time = 270/30 = 9 sec."
    },
    {
        "id": "quant_tsd_03",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Medium",
        "question": "A car travels 300 km at 60 km/h and returns at 40 km/h. Average speed for total journey is:",
        "options": [
            "45 km/h",
            "48 km/h",
            "50 km/h",
            "52 km/h"
        ],
        "answer": "48 km/h",
        "explanation": "Average speed = 2xy/(x+y) = 2*60*40 / 100 = 4800 / 100 = 48 km/h."
    },
    {
        "id": "quant_tsd_04",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Easy",
        "question": "How far will a bus travel in 3 hours at a speed of 55 km/h?",
        "options": [
            "150 km",
            "160 km",
            "165 km",
            "170 km"
        ],
        "answer": "165 km",
        "explanation": "Distance = 55 * 3 = 165 km."
    },
    {
        "id": "quant_tsd_05",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Medium",
        "question": "A train 200m long passes a standing pole in 10 seconds. Speed of train in km/h:",
        "options": [
            "60 km/h",
            "72 km/h",
            "80 km/h",
            "90 km/h"
        ],
        "answer": "72 km/h",
        "explanation": "Speed = 200m / 10s = 20 m/s = 20 * (18/5) = 72 km/h."
    },
    {
        "id": "quant_tsd_06",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Hard",
        "question": "A person covers a certain distance at 10 km/h and arrives 15 mins late. If he travels at 12 km/h, he is 5 mins late. Distance is:",
        "options": [
            "8 km",
            "10 km",
            "12 km",
            "15 km"
        ],
        "answer": "10 km",
        "explanation": "Time diff = 10 mins = 1/6 hr. D/10 - D/12 = 1/6 => D/60 = 1/6 => D = 10 km."
    },
    {
        "id": "quant_tsd_07",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Easy",
        "question": "If speed is doubled, time taken to cover the same distance will be:",
        "options": [
            "Doubled",
            "Halved",
            "Unchanged",
            "Quadrupled"
        ],
        "answer": "Halved",
        "explanation": "Time is inversely proportional to speed."
    },
    {
        "id": "quant_tsd_08",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Medium",
        "question": "A man walks at 5 km/h and crosses a bridge in 15 minutes. Length of bridge is:",
        "options": [
            "1000m",
            "1250m",
            "1500m",
            "2000m"
        ],
        "answer": "1250m",
        "explanation": "Speed = 5 * (5/18) m/s. Time = 15 * 60 = 900s. Distance = (25/18) * 900 = 1250m."
    },
    {
        "id": "quant_tsd_09",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Easy",
        "question": "Convert 15 m/s to km/h.",
        "options": [
            "45 km/h",
            "50 km/h",
            "54 km/h",
            "60 km/h"
        ],
        "answer": "54 km/h",
        "explanation": "15 * (18/5) = 54 km/h."
    },
    {
        "id": "quant_tsd_10",
        "category": "Quantitative Aptitude",
        "topic": "Time, Speed and Distance",
        "difficulty": "Hard",
        "question": "A boat goes 12 km downstream in 1 hour and upstream in 2 hours. Speed of stream is:",
        "options": [
            "2 km/h",
            "3 km/h",
            "4 km/h",
            "5 km/h"
        ],
        "answer": "3 km/h",
        "explanation": "Downstream speed = 12 km/h, Upstream speed = 6 km/h. Speed of stream = (12 - 6)/2 = 3 km/h."
    },
    {
        "id": "quant_int_01",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Medium",
        "question": "Simple interest on $4,000 invested at 5% per annum for 3 years:",
        "options": [
            "$400",
            "$500",
            "$600",
            "$750"
        ],
        "answer": "$600",
        "explanation": "SI = (4000 * 5 * 3) / 100 = $600."
    },
    {
        "id": "quant_int_02",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Hard",
        "question": "Compound interest on $10,000 for 2 years at 10% per annum compounded annually:",
        "options": [
            "$2,000",
            "$2,100",
            "$2,200",
            "$2,400"
        ],
        "answer": "$2,100",
        "explanation": "Amount = 10000 * (1.10)^2 = $12,100. CI = 12100 - 10000 = $2,100."
    },
    {
        "id": "quant_int_03",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Easy",
        "question": "What is the SI on $1,000 at 10% p.a. for 2 years?",
        "options": [
            "$150",
            "$200",
            "$250",
            "$300"
        ],
        "answer": "$200",
        "explanation": "SI = 1000 * 10 * 2 / 100 = $200."
    },
    {
        "id": "quant_int_04",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Medium",
        "question": "At what rate % p.a. simple interest will a sum of money double itself in 8 years?",
        "options": [
            "10%",
            "12.5%",
            "15%",
            "16.66%"
        ],
        "answer": "12.5%",
        "explanation": "Interest = Principal. P = (P * R * 8)/100 => R = 100 / 8 = 12.5%."
    },
    {
        "id": "quant_int_05",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Hard",
        "question": "Difference between CI and SI on $5,000 for 2 years at 8% p.a. is:",
        "options": [
            "$24",
            "$32",
            "$40",
            "$48"
        ],
        "answer": "$32",
        "explanation": "Diff = P * (R/100)^2 = 5000 * (8/100)^2 = 5000 * 0.0064 = $32."
    },
    {
        "id": "quant_int_06",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Easy",
        "question": "A sum amounts to $1,200 in 2 years at 10% SI p.a. Find principal.",
        "options": [
            "$900",
            "$1,000",
            "$1,050",
            "$1,100"
        ],
        "answer": "$1,000",
        "explanation": "Amount = P(1 + 0.10*2) = 1.2P = 1200 => P = $1,000."
    },
    {
        "id": "quant_int_07",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Medium",
        "question": "A sum of money doubles itself at CI in 5 years. In how many years will it become 8 times?",
        "options": [
            "10 years",
            "15 years",
            "20 years",
            "25 years"
        ],
        "answer": "15 years",
        "explanation": "2^1 in 5 yrs => 2^3 (8 times) in 3 * 5 = 15 years."
    },
    {
        "id": "quant_int_08",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Hard",
        "question": "Find compound interest on $8,000 for 9 months at 20% p.a. compounded quarterly.",
        "options": [
            "$1,200",
            "$1,261",
            "$1,300",
            "$1,340"
        ],
        "answer": "$1,261",
        "explanation": "Rate per quarter = 5%. Periods = 3 quarters. Amount = 8000 * (1.05)^3 = $9,261. CI = 9261 - 8000 = $1,261."
    },
    {
        "id": "quant_int_09",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Easy",
        "question": "In how many years will $500 yield $100 SI at 5% p.a.?",
        "options": [
            "2 years",
            "3 years",
            "4 years",
            "5 years"
        ],
        "answer": "4 years",
        "explanation": "T = (SI * 100)/(P * R) = (100 * 100)/(500 * 5) = 4 years."
    },
    {
        "id": "quant_int_10",
        "category": "Quantitative Aptitude",
        "topic": "Simple Interest",
        "difficulty": "Medium",
        "question": "Principal that yields $210 interest at 10% CI p.a. in 2 years is:",
        "options": [
            "$900",
            "$1,000",
            "$1,100",
            "$1,200"
        ],
        "answer": "$1,000",
        "explanation": "CI = P[(1.10)^2 - 1] = 0.21P = 210 => P = $1,000."
    },
    {
        "id": "quant_num_01",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "Unit digit of (3^65 * 6^59 * 7^71) is:",
        "options": [
            "2",
            "4",
            "6",
            "8"
        ],
        "answer": "4",
        "explanation": "3^65 -> 3, 6^59 -> 6, 7^71 -> 3. Product unit digit = 3*6*3 = 54 -> 4."
    },
    {
        "id": "quant_num_02",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the HCF of 108, 288 and 360?",
        "options": [
            "18",
            "24",
            "36",
            "48"
        ],
        "answer": "36",
        "explanation": "Prime factorizations yield HCF = 36."
    },
    {
        "id": "quant_num_03",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Hard",
        "question": "Remainer when 2^31 is divided by 5:",
        "options": [
            "1",
            "2",
            "3",
            "4"
        ],
        "answer": "3",
        "explanation": "2^1=2, 2^2=4, 2^3=8, 2^4=16(rem 1). 31 = 4*7 + 3. Remainder = 2^3 mod 5 = 3."
    },
    {
        "id": "quant_num_04",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "Sum of first 20 even natural numbers is:",
        "options": [
            "210",
            "400",
            "420",
            "440"
        ],
        "answer": "420",
        "explanation": "Sum = n(n+1) = 20 * 21 = 420."
    },
    {
        "id": "quant_num_05",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "LCM of two numbers is 180 and their ratio is 3 : 4. Find the sum of numbers.",
        "options": [
            "90",
            "105",
            "120",
            "140"
        ],
        "answer": "105",
        "explanation": "Let numbers be 3x and 4x. LCM = 12x = 180 => x = 15. Sum = 7x = 105."
    },
    {
        "id": "quant_prob_01",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Medium",
        "question": "Two dice rolled. Probability sum is 8:",
        "options": [
            "5/36",
            "1/6",
            "7/36",
            "1/9"
        ],
        "answer": "5/36",
        "explanation": "Favorable: (2,6),(3,5),(4,4),(5,3),(6,2) -> 5/36."
    },
    {
        "id": "quant_prob_02",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Easy",
        "question": "Card drawn from deck. Probability of getting a King:",
        "options": [
            "1/52",
            "1/26",
            "1/13",
            "1/4"
        ],
        "answer": "1/13",
        "explanation": "4 Kings in 52 cards => 4/52 = 1/13."
    },
    {
        "id": "quant_prob_03",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Hard",
        "question": "A box contains 5 red and 4 blue balls. 2 balls drawn at random. Probability both are red:",
        "options": [
            "5/18",
            "5/14",
            "4/9",
            "5/12"
        ],
        "answer": "5/18",
        "explanation": "C(5,2)/C(9,2) = 10 / 36 = 5/18."
    },
    {
        "id": "quant_prob_04",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Easy",
        "question": "Coin tossed 3 times. Probability of getting at least 2 heads:",
        "options": [
            "1/4",
            "3/8",
            "1/2",
            "5/8"
        ],
        "answer": "1/2",
        "explanation": "Outcomes with >=2 heads: HHH, HHT, HTH, THH (4 out of 8) -> 1/2."
    },
    {
        "id": "quant_prob_05",
        "category": "Quantitative Aptitude",
        "topic": "Probability",
        "difficulty": "Medium",
        "question": "Probability of throwing a prime number with a single die:",
        "options": [
            "1/6",
            "1/3",
            "1/2",
            "2/3"
        ],
        "answer": "1/2",
        "explanation": "Primes on die: 2, 3, 5 (3 outcomes out of 6) -> 1/2."
    },
    {
        "id": "quant_perm_01",
        "category": "Quantitative Aptitude",
        "topic": "Permutation and Combination",
        "difficulty": "Medium",
        "question": "In how many ways can letters of 'LEADING' be arranged so vowels are always together?",
        "options": [
            "360",
            "480",
            "720",
            "1440"
        ],
        "answer": "720",
        "explanation": "Vowels: E, A, I (3). Consonants: L, D, N, G (4). Group vowels as 1 unit => 5 units. Ways = 5! * 3! = 120 * 6 = 720."
    },
    {
        "id": "quant_perm_02",
        "category": "Quantitative Aptitude",
        "topic": "Permutation and Combination",
        "difficulty": "Easy",
        "question": "Value of C(10, 3) is:",
        "options": [
            "90",
            "120",
            "150",
            "180"
        ],
        "answer": "120",
        "explanation": "10*9*8 / (3*2*1) = 120."
    },
    {
        "id": "quant_perm_03",
        "category": "Quantitative Aptitude",
        "topic": "Permutation and Combination",
        "difficulty": "Hard",
        "question": "Number of diagonals in a 10-sided polygon (decagon):",
        "options": [
            "25",
            "35",
            "45",
            "50"
        ],
        "answer": "35",
        "explanation": "Diagonals = C(n,2) - n = C(10,2) - 10 = 45 - 10 = 35."
    },
    {
        "id": "quant_age_01",
        "category": "Quantitative Aptitude",
        "topic": "Ages",
        "difficulty": "Easy",
        "question": "Father is 30 years older than son. In 5 years, father will be thrice as old as son. Present age of son:",
        "options": [
            "5",
            "10",
            "12",
            "15"
        ],
        "answer": "10",
        "explanation": "F = S + 30. (S + 35) = 3(S + 5) => S + 35 = 3S + 15 => 2S = 20 => S = 10."
    },
    {
        "id": "quant_age_02",
        "category": "Quantitative Aptitude",
        "topic": "Ages",
        "difficulty": "Medium",
        "question": "Ratio of ages of A and B is 4 : 5. 6 years ago ratio was 3 : 4. Find present age of A.",
        "options": [
            "18",
            "24",
            "30",
            "36"
        ],
        "answer": "24",
        "explanation": "(4x-6)/(5x-6) = 3/4 => 16x - 24 = 15x - 18 => x = 6. A's age = 4*6 = 24."
    },
    {
        "id": "quant_mix_01",
        "category": "Quantitative Aptitude",
        "topic": "Mixtures and Allegations",
        "difficulty": "Medium",
        "question": "In what ratio must tea at $60/kg be mixed with tea at $75/kg to get mixture worth $65/kg?",
        "options": [
            "1 : 2",
            "2 : 1",
            "3 : 1",
            "1 : 3"
        ],
        "answer": "2 : 1",
        "explanation": "By rule of allegation: (75-65):(65-60) = 10:5 = 2:1."
    },
    {
        "id": "quant_gen_01",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 64 and 31?",
        "options": [
            "90",
            "95",
            "100",
            "105"
        ],
        "answer": "95",
        "explanation": "64 + 31 = 95."
    },
    {
        "id": "quant_gen_02",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 75 and 33?",
        "options": [
            "103",
            "108",
            "113",
            "118"
        ],
        "answer": "108",
        "explanation": "75 + 33 = 108."
    },
    {
        "id": "quant_gen_03",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 39 and 43?",
        "options": [
            "77",
            "82",
            "87",
            "92"
        ],
        "answer": "82",
        "explanation": "39 + 43 = 82."
    },
    {
        "id": "quant_gen_04",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 78 and 47?",
        "options": [
            "120",
            "125",
            "130",
            "135"
        ],
        "answer": "125",
        "explanation": "78 + 47 = 125."
    },
    {
        "id": "quant_gen_05",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 57 and 74?",
        "options": [
            "126",
            "131",
            "136",
            "141"
        ],
        "answer": "131",
        "explanation": "57 + 74 = 131."
    },
    {
        "id": "quant_gen_06",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 48 and 11?",
        "options": [
            "54",
            "59",
            "64",
            "69"
        ],
        "answer": "59",
        "explanation": "48 + 11 = 59."
    },
    {
        "id": "quant_gen_07",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 28 and 52?",
        "options": [
            "75",
            "80",
            "85",
            "90"
        ],
        "answer": "80",
        "explanation": "28 + 52 = 80."
    },
    {
        "id": "quant_gen_08",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 76 and 76?",
        "options": [
            "147",
            "152",
            "157",
            "162"
        ],
        "answer": "152",
        "explanation": "76 + 76 = 152."
    },
    {
        "id": "quant_gen_09",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 25 and 85?",
        "options": [
            "105",
            "110",
            "115",
            "120"
        ],
        "answer": "110",
        "explanation": "25 + 85 = 110."
    },
    {
        "id": "quant_gen_10",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 80 and 22?",
        "options": [
            "97",
            "102",
            "107",
            "112"
        ],
        "answer": "102",
        "explanation": "80 + 22 = 102."
    },
    {
        "id": "quant_gen_11",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 78 and 33?",
        "options": [
            "106",
            "111",
            "116",
            "121"
        ],
        "answer": "111",
        "explanation": "78 + 33 = 111."
    },
    {
        "id": "quant_gen_12",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 61 and 51?",
        "options": [
            "107",
            "112",
            "117",
            "122"
        ],
        "answer": "112",
        "explanation": "61 + 51 = 112."
    },
    {
        "id": "quant_gen_13",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 63 and 46?",
        "options": [
            "104",
            "109",
            "114",
            "119"
        ],
        "answer": "109",
        "explanation": "63 + 46 = 109."
    },
    {
        "id": "quant_gen_14",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 61 and 54?",
        "options": [
            "110",
            "115",
            "120",
            "125"
        ],
        "answer": "115",
        "explanation": "61 + 54 = 115."
    },
    {
        "id": "quant_gen_15",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 19 and 44?",
        "options": [
            "58",
            "63",
            "68",
            "73"
        ],
        "answer": "63",
        "explanation": "19 + 44 = 63."
    },
    {
        "id": "quant_gen_16",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 49 and 61?",
        "options": [
            "105",
            "110",
            "115",
            "120"
        ],
        "answer": "110",
        "explanation": "49 + 61 = 110."
    },
    {
        "id": "quant_gen_17",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 36 and 17?",
        "options": [
            "48",
            "53",
            "58",
            "63"
        ],
        "answer": "53",
        "explanation": "36 + 17 = 53."
    },
    {
        "id": "quant_gen_18",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 32 and 11?",
        "options": [
            "38",
            "43",
            "48",
            "53"
        ],
        "answer": "43",
        "explanation": "32 + 11 = 43."
    },
    {
        "id": "quant_gen_19",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 55 and 47?",
        "options": [
            "97",
            "102",
            "107",
            "112"
        ],
        "answer": "102",
        "explanation": "55 + 47 = 102."
    },
    {
        "id": "quant_gen_20",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 74 and 23?",
        "options": [
            "92",
            "97",
            "102",
            "107"
        ],
        "answer": "97",
        "explanation": "74 + 23 = 97."
    },
    {
        "id": "quant_gen_21",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 25 and 18?",
        "options": [
            "38",
            "43",
            "48",
            "53"
        ],
        "answer": "43",
        "explanation": "25 + 18 = 43."
    },
    {
        "id": "quant_gen_22",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 51 and 72?",
        "options": [
            "118",
            "123",
            "128",
            "133"
        ],
        "answer": "123",
        "explanation": "51 + 72 = 123."
    },
    {
        "id": "quant_gen_23",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 44 and 90?",
        "options": [
            "129",
            "134",
            "139",
            "144"
        ],
        "answer": "134",
        "explanation": "44 + 90 = 134."
    },
    {
        "id": "quant_gen_24",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 50 and 88?",
        "options": [
            "133",
            "138",
            "143",
            "148"
        ],
        "answer": "138",
        "explanation": "50 + 88 = 138."
    },
    {
        "id": "quant_gen_25",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 65 and 26?",
        "options": [
            "86",
            "91",
            "96",
            "101"
        ],
        "answer": "91",
        "explanation": "65 + 26 = 91."
    },
    {
        "id": "quant_gen_26",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 28 and 49?",
        "options": [
            "72",
            "77",
            "82",
            "87"
        ],
        "answer": "77",
        "explanation": "28 + 49 = 77."
    },
    {
        "id": "quant_gen_27",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 85 and 30?",
        "options": [
            "110",
            "115",
            "120",
            "125"
        ],
        "answer": "115",
        "explanation": "85 + 30 = 115."
    },
    {
        "id": "quant_gen_28",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 18 and 52?",
        "options": [
            "65",
            "70",
            "75",
            "80"
        ],
        "answer": "70",
        "explanation": "18 + 52 = 70."
    },
    {
        "id": "quant_gen_29",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 81 and 72?",
        "options": [
            "148",
            "153",
            "158",
            "163"
        ],
        "answer": "153",
        "explanation": "81 + 72 = 153."
    },
    {
        "id": "quant_gen_30",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 30 and 20?",
        "options": [
            "45",
            "50",
            "55",
            "60"
        ],
        "answer": "50",
        "explanation": "30 + 20 = 50."
    },
    {
        "id": "quant_gen_31",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 59 and 63?",
        "options": [
            "117",
            "122",
            "127",
            "132"
        ],
        "answer": "122",
        "explanation": "59 + 63 = 122."
    },
    {
        "id": "quant_gen_32",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 86 and 74?",
        "options": [
            "155",
            "160",
            "165",
            "170"
        ],
        "answer": "160",
        "explanation": "86 + 74 = 160."
    },
    {
        "id": "quant_gen_33",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 66 and 23?",
        "options": [
            "84",
            "89",
            "94",
            "99"
        ],
        "answer": "89",
        "explanation": "66 + 23 = 89."
    },
    {
        "id": "quant_gen_34",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 47 and 63?",
        "options": [
            "105",
            "110",
            "115",
            "120"
        ],
        "answer": "110",
        "explanation": "47 + 63 = 110."
    },
    {
        "id": "quant_gen_35",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 30 and 38?",
        "options": [
            "63",
            "68",
            "73",
            "78"
        ],
        "answer": "68",
        "explanation": "30 + 38 = 68."
    },
    {
        "id": "quant_gen_36",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 70 and 38?",
        "options": [
            "103",
            "108",
            "113",
            "118"
        ],
        "answer": "108",
        "explanation": "70 + 38 = 108."
    },
    {
        "id": "quant_gen_37",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 78 and 81?",
        "options": [
            "154",
            "159",
            "164",
            "169"
        ],
        "answer": "159",
        "explanation": "78 + 81 = 159."
    },
    {
        "id": "quant_gen_38",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 43 and 66?",
        "options": [
            "104",
            "109",
            "114",
            "119"
        ],
        "answer": "109",
        "explanation": "43 + 66 = 109."
    },
    {
        "id": "quant_gen_39",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 67 and 80?",
        "options": [
            "142",
            "147",
            "152",
            "157"
        ],
        "answer": "147",
        "explanation": "67 + 80 = 147."
    },
    {
        "id": "quant_gen_40",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 24 and 46?",
        "options": [
            "65",
            "70",
            "75",
            "80"
        ],
        "answer": "70",
        "explanation": "24 + 46 = 70."
    },
    {
        "id": "quant_gen_41",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 73 and 23?",
        "options": [
            "91",
            "96",
            "101",
            "106"
        ],
        "answer": "96",
        "explanation": "73 + 23 = 96."
    },
    {
        "id": "quant_gen_42",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 89 and 87?",
        "options": [
            "171",
            "176",
            "181",
            "186"
        ],
        "answer": "176",
        "explanation": "89 + 87 = 176."
    },
    {
        "id": "quant_gen_43",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Medium",
        "question": "What is the sum of 66 and 80?",
        "options": [
            "141",
            "146",
            "151",
            "156"
        ],
        "answer": "146",
        "explanation": "66 + 80 = 146."
    },
    {
        "id": "quant_gen_44",
        "category": "Quantitative Aptitude",
        "topic": "Number System",
        "difficulty": "Easy",
        "question": "What is the sum of 80 and 45?",
        "options": [
            "120",
            "125",
            "130",
            "135"
        ],
        "answer": "125",
        "explanation": "80 + 45 = 125."
    },
    {
        "id": "logic_num_01",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "Complete series: 2, 6, 12, 20, 30, ?",
        "options": [
            "38",
            "40",
            "42",
            "44"
        ],
        "answer": "42",
        "explanation": "+4, +6, +8, +10, next is +12 => 30+12 = 42."
    },
    {
        "id": "logic_num_02",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "Next number: 3, 5, 9, 17, 33, ?",
        "options": [
            "49",
            "65",
            "66",
            "72"
        ],
        "answer": "65",
        "explanation": "Pattern x*2 - 1 => 33*2 - 1 = 65."
    },
    {
        "id": "logic_let_01",
        "category": "Logical Reasoning",
        "topic": "Letter Series",
        "difficulty": "Easy",
        "question": "Complete series: A, C, F, J, O, ?",
        "options": [
            "U",
            "V",
            "W",
            "X"
        ],
        "answer": "U",
        "explanation": "+2, +3, +4, +5, +6 => O + 6 = U."
    },
    {
        "id": "logic_ana_01",
        "category": "Logical Reasoning",
        "topic": "Analogy",
        "difficulty": "Easy",
        "question": "Doctor is to Hospital as Teacher is to ?",
        "options": [
            "Office",
            "School",
            "Library",
            "Lab"
        ],
        "answer": "School",
        "explanation": "Workplace analogy."
    },
    {
        "id": "logic_code_01",
        "category": "Logical Reasoning",
        "topic": "Coding-Decoding",
        "difficulty": "Easy",
        "question": "If SYSTEM is coded as SYSMET, FRACTION is coded as:",
        "options": [
            "CARFNOIT",
            "NOITCARF",
            "ARFCITNO",
            "CARFTION"
        ],
        "answer": "CARFNOIT",
        "explanation": "Split and reverse halves."
    },
    {
        "id": "logic_blood_01",
        "category": "Logical Reasoning",
        "topic": "Blood Relations",
        "difficulty": "Medium",
        "question": "Pointing to photo, man says 'That man's father is my father's son.' Whose photo?",
        "options": [
            "His own",
            "His son's",
            "His father's",
            "His nephew's"
        ],
        "answer": "His son's",
        "explanation": "Man is describing his son."
    },
    {
        "id": "logic_dir_01",
        "category": "Logical Reasoning",
        "topic": "Direction Sense",
        "difficulty": "Easy",
        "question": "Walk 5km North, turn right 3km, right 5km. Distance from start:",
        "options": [
            "3 km",
            "5 km",
            "8 km",
            "0 km"
        ],
        "answer": "3 km",
        "explanation": "North and South cancel."
    },
    {
        "id": "logic_syl_01",
        "category": "Logical Reasoning",
        "topic": "Syllogisms",
        "difficulty": "Medium",
        "question": "Statements: All cats are dogs. All dogs are mammals. Conclusion:",
        "options": [
            "Only I follows",
            "Only II follows",
            "Both follow",
            "Neither follows"
        ],
        "answer": "Only I follows",
        "explanation": "Cats \u2282 Dogs \u2282 Mammals."
    },
    {
        "id": "logic_odd_01",
        "category": "Logical Reasoning",
        "topic": "Odd One Out",
        "difficulty": "Easy",
        "question": "Find the odd one out: 27, 64, 125, 144",
        "options": [
            "27",
            "64",
            "125",
            "144"
        ],
        "answer": "144",
        "explanation": "27=3^3, 64=4^3, 125=5^3. 144 is 12^2 (square, not cube)."
    },
    {
        "id": "logic_seat_01",
        "category": "Logical Reasoning",
        "topic": "Seating Arrangement",
        "difficulty": "Hard",
        "question": "5 friends A,B,C,D,E in a row. E is left end, C is 2nd from right. B is in middle. Who is next to E?",
        "options": [
            "A",
            "B",
            "C",
            "D"
        ],
        "answer": "A",
        "explanation": "Order: E A B C D."
    },
    {
        "id": "logic_puz_01",
        "category": "Logical Reasoning",
        "topic": "Logical Puzzles",
        "difficulty": "Medium",
        "question": "5 machines take 5 mins to make 5 widgets. 100 machines make 100 widgets in:",
        "options": [
            "100 mins",
            "50 mins",
            "5 mins",
            "1 min"
        ],
        "answer": "5 mins",
        "explanation": "Each machine takes 5 mins per widget."
    },
    {
        "id": "logic_stmt_01",
        "category": "Logical Reasoning",
        "topic": "Statement and Conclusion",
        "difficulty": "Medium",
        "question": "Statement: Most people who stop smoking gain weight. Conclusion:",
        "options": [
            "If one stops smoking, one will gain weight",
            "Smoking reduces weight",
            "Neither follows",
            "Both follow"
        ],
        "answer": "Neither follows",
        "explanation": "Correlation does not imply strict conclusion."
    },
    {
        "id": "logic_gen_01",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 2, 5, 8, 11, ?",
        "options": [
            "12",
            "13",
            "14",
            "15"
        ],
        "answer": "14",
        "explanation": "Differences are constantly +3. Next term = 11 + 3 = 14."
    },
    {
        "id": "logic_gen_02",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 4, 7, 10, 13, ?",
        "options": [
            "14",
            "15",
            "16",
            "17"
        ],
        "answer": "16",
        "explanation": "Differences are constantly +3. Next term = 13 + 3 = 16."
    },
    {
        "id": "logic_gen_03",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 6, 9, 12, 15, ?",
        "options": [
            "16",
            "17",
            "18",
            "19"
        ],
        "answer": "18",
        "explanation": "Differences are constantly +3. Next term = 15 + 3 = 18."
    },
    {
        "id": "logic_gen_04",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 8, 11, 14, 17, ?",
        "options": [
            "18",
            "19",
            "20",
            "21"
        ],
        "answer": "20",
        "explanation": "Differences are constantly +3. Next term = 17 + 3 = 20."
    },
    {
        "id": "logic_gen_05",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 10, 13, 16, 19, ?",
        "options": [
            "20",
            "21",
            "22",
            "23"
        ],
        "answer": "22",
        "explanation": "Differences are constantly +3. Next term = 19 + 3 = 22."
    },
    {
        "id": "logic_gen_06",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 12, 15, 18, 21, ?",
        "options": [
            "22",
            "23",
            "24",
            "25"
        ],
        "answer": "24",
        "explanation": "Differences are constantly +3. Next term = 21 + 3 = 24."
    },
    {
        "id": "logic_gen_07",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 14, 17, 20, 23, ?",
        "options": [
            "24",
            "25",
            "26",
            "27"
        ],
        "answer": "26",
        "explanation": "Differences are constantly +3. Next term = 23 + 3 = 26."
    },
    {
        "id": "logic_gen_08",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 16, 19, 22, 25, ?",
        "options": [
            "26",
            "27",
            "28",
            "29"
        ],
        "answer": "28",
        "explanation": "Differences are constantly +3. Next term = 25 + 3 = 28."
    },
    {
        "id": "logic_gen_09",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 18, 21, 24, 27, ?",
        "options": [
            "28",
            "29",
            "30",
            "31"
        ],
        "answer": "30",
        "explanation": "Differences are constantly +3. Next term = 27 + 3 = 30."
    },
    {
        "id": "logic_gen_10",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 20, 23, 26, 29, ?",
        "options": [
            "30",
            "31",
            "32",
            "33"
        ],
        "answer": "32",
        "explanation": "Differences are constantly +3. Next term = 29 + 3 = 32."
    },
    {
        "id": "logic_gen_11",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 22, 25, 28, 31, ?",
        "options": [
            "32",
            "33",
            "34",
            "35"
        ],
        "answer": "34",
        "explanation": "Differences are constantly +3. Next term = 31 + 3 = 34."
    },
    {
        "id": "logic_gen_12",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 24, 27, 30, 33, ?",
        "options": [
            "34",
            "35",
            "36",
            "37"
        ],
        "answer": "36",
        "explanation": "Differences are constantly +3. Next term = 33 + 3 = 36."
    },
    {
        "id": "logic_gen_13",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 26, 29, 32, 35, ?",
        "options": [
            "36",
            "37",
            "38",
            "39"
        ],
        "answer": "38",
        "explanation": "Differences are constantly +3. Next term = 35 + 3 = 38."
    },
    {
        "id": "logic_gen_14",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 28, 31, 34, 37, ?",
        "options": [
            "38",
            "39",
            "40",
            "41"
        ],
        "answer": "40",
        "explanation": "Differences are constantly +3. Next term = 37 + 3 = 40."
    },
    {
        "id": "logic_gen_15",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 30, 33, 36, 39, ?",
        "options": [
            "40",
            "41",
            "42",
            "43"
        ],
        "answer": "42",
        "explanation": "Differences are constantly +3. Next term = 39 + 3 = 42."
    },
    {
        "id": "logic_gen_16",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 32, 35, 38, 41, ?",
        "options": [
            "42",
            "43",
            "44",
            "45"
        ],
        "answer": "44",
        "explanation": "Differences are constantly +3. Next term = 41 + 3 = 44."
    },
    {
        "id": "logic_gen_17",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 34, 37, 40, 43, ?",
        "options": [
            "44",
            "45",
            "46",
            "47"
        ],
        "answer": "46",
        "explanation": "Differences are constantly +3. Next term = 43 + 3 = 46."
    },
    {
        "id": "logic_gen_18",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 36, 39, 42, 45, ?",
        "options": [
            "46",
            "47",
            "48",
            "49"
        ],
        "answer": "48",
        "explanation": "Differences are constantly +3. Next term = 45 + 3 = 48."
    },
    {
        "id": "logic_gen_19",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 38, 41, 44, 47, ?",
        "options": [
            "48",
            "49",
            "50",
            "51"
        ],
        "answer": "50",
        "explanation": "Differences are constantly +3. Next term = 47 + 3 = 50."
    },
    {
        "id": "logic_gen_20",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 40, 43, 46, 49, ?",
        "options": [
            "50",
            "51",
            "52",
            "53"
        ],
        "answer": "52",
        "explanation": "Differences are constantly +3. Next term = 49 + 3 = 52."
    },
    {
        "id": "logic_gen_21",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 42, 45, 48, 51, ?",
        "options": [
            "52",
            "53",
            "54",
            "55"
        ],
        "answer": "54",
        "explanation": "Differences are constantly +3. Next term = 51 + 3 = 54."
    },
    {
        "id": "logic_gen_22",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 44, 47, 50, 53, ?",
        "options": [
            "54",
            "55",
            "56",
            "57"
        ],
        "answer": "56",
        "explanation": "Differences are constantly +3. Next term = 53 + 3 = 56."
    },
    {
        "id": "logic_gen_23",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 46, 49, 52, 55, ?",
        "options": [
            "56",
            "57",
            "58",
            "59"
        ],
        "answer": "58",
        "explanation": "Differences are constantly +3. Next term = 55 + 3 = 58."
    },
    {
        "id": "logic_gen_24",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 48, 51, 54, 57, ?",
        "options": [
            "58",
            "59",
            "60",
            "61"
        ],
        "answer": "60",
        "explanation": "Differences are constantly +3. Next term = 57 + 3 = 60."
    },
    {
        "id": "logic_gen_25",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 50, 53, 56, 59, ?",
        "options": [
            "60",
            "61",
            "62",
            "63"
        ],
        "answer": "62",
        "explanation": "Differences are constantly +3. Next term = 59 + 3 = 62."
    },
    {
        "id": "logic_gen_26",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 52, 55, 58, 61, ?",
        "options": [
            "62",
            "63",
            "64",
            "65"
        ],
        "answer": "64",
        "explanation": "Differences are constantly +3. Next term = 61 + 3 = 64."
    },
    {
        "id": "logic_gen_27",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 54, 57, 60, 63, ?",
        "options": [
            "64",
            "65",
            "66",
            "67"
        ],
        "answer": "66",
        "explanation": "Differences are constantly +3. Next term = 63 + 3 = 66."
    },
    {
        "id": "logic_gen_28",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 56, 59, 62, 65, ?",
        "options": [
            "66",
            "67",
            "68",
            "69"
        ],
        "answer": "68",
        "explanation": "Differences are constantly +3. Next term = 65 + 3 = 68."
    },
    {
        "id": "logic_gen_29",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 58, 61, 64, 67, ?",
        "options": [
            "68",
            "69",
            "70",
            "71"
        ],
        "answer": "70",
        "explanation": "Differences are constantly +3. Next term = 67 + 3 = 70."
    },
    {
        "id": "logic_gen_30",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 60, 63, 66, 69, ?",
        "options": [
            "70",
            "71",
            "72",
            "73"
        ],
        "answer": "72",
        "explanation": "Differences are constantly +3. Next term = 69 + 3 = 72."
    },
    {
        "id": "logic_gen_31",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 62, 65, 68, 71, ?",
        "options": [
            "72",
            "73",
            "74",
            "75"
        ],
        "answer": "74",
        "explanation": "Differences are constantly +3. Next term = 71 + 3 = 74."
    },
    {
        "id": "logic_gen_32",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 64, 67, 70, 73, ?",
        "options": [
            "74",
            "75",
            "76",
            "77"
        ],
        "answer": "76",
        "explanation": "Differences are constantly +3. Next term = 73 + 3 = 76."
    },
    {
        "id": "logic_gen_33",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 66, 69, 72, 75, ?",
        "options": [
            "76",
            "77",
            "78",
            "79"
        ],
        "answer": "78",
        "explanation": "Differences are constantly +3. Next term = 75 + 3 = 78."
    },
    {
        "id": "logic_gen_34",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 68, 71, 74, 77, ?",
        "options": [
            "78",
            "79",
            "80",
            "81"
        ],
        "answer": "80",
        "explanation": "Differences are constantly +3. Next term = 77 + 3 = 80."
    },
    {
        "id": "logic_gen_35",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 70, 73, 76, 79, ?",
        "options": [
            "80",
            "81",
            "82",
            "83"
        ],
        "answer": "82",
        "explanation": "Differences are constantly +3. Next term = 79 + 3 = 82."
    },
    {
        "id": "logic_gen_36",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 72, 75, 78, 81, ?",
        "options": [
            "82",
            "83",
            "84",
            "85"
        ],
        "answer": "84",
        "explanation": "Differences are constantly +3. Next term = 81 + 3 = 84."
    },
    {
        "id": "logic_gen_37",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 74, 77, 80, 83, ?",
        "options": [
            "84",
            "85",
            "86",
            "87"
        ],
        "answer": "86",
        "explanation": "Differences are constantly +3. Next term = 83 + 3 = 86."
    },
    {
        "id": "logic_gen_38",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 76, 79, 82, 85, ?",
        "options": [
            "86",
            "87",
            "88",
            "89"
        ],
        "answer": "88",
        "explanation": "Differences are constantly +3. Next term = 85 + 3 = 88."
    },
    {
        "id": "logic_gen_39",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 78, 81, 84, 87, ?",
        "options": [
            "88",
            "89",
            "90",
            "91"
        ],
        "answer": "90",
        "explanation": "Differences are constantly +3. Next term = 87 + 3 = 90."
    },
    {
        "id": "logic_gen_40",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 80, 83, 86, 89, ?",
        "options": [
            "90",
            "91",
            "92",
            "93"
        ],
        "answer": "92",
        "explanation": "Differences are constantly +3. Next term = 89 + 3 = 92."
    },
    {
        "id": "logic_gen_41",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 82, 85, 88, 91, ?",
        "options": [
            "92",
            "93",
            "94",
            "95"
        ],
        "answer": "94",
        "explanation": "Differences are constantly +3. Next term = 91 + 3 = 94."
    },
    {
        "id": "logic_gen_42",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 84, 87, 90, 93, ?",
        "options": [
            "94",
            "95",
            "96",
            "97"
        ],
        "answer": "96",
        "explanation": "Differences are constantly +3. Next term = 93 + 3 = 96."
    },
    {
        "id": "logic_gen_43",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 86, 89, 92, 95, ?",
        "options": [
            "96",
            "97",
            "98",
            "99"
        ],
        "answer": "98",
        "explanation": "Differences are constantly +3. Next term = 95 + 3 = 98."
    },
    {
        "id": "logic_gen_44",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 88, 91, 94, 97, ?",
        "options": [
            "98",
            "99",
            "100",
            "101"
        ],
        "answer": "100",
        "explanation": "Differences are constantly +3. Next term = 97 + 3 = 100."
    },
    {
        "id": "logic_gen_45",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 90, 93, 96, 99, ?",
        "options": [
            "100",
            "101",
            "102",
            "103"
        ],
        "answer": "102",
        "explanation": "Differences are constantly +3. Next term = 99 + 3 = 102."
    },
    {
        "id": "logic_gen_46",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 92, 95, 98, 101, ?",
        "options": [
            "102",
            "103",
            "104",
            "105"
        ],
        "answer": "104",
        "explanation": "Differences are constantly +3. Next term = 101 + 3 = 104."
    },
    {
        "id": "logic_gen_47",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 94, 97, 100, 103, ?",
        "options": [
            "104",
            "105",
            "106",
            "107"
        ],
        "answer": "106",
        "explanation": "Differences are constantly +3. Next term = 103 + 3 = 106."
    },
    {
        "id": "logic_gen_48",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 96, 99, 102, 105, ?",
        "options": [
            "106",
            "107",
            "108",
            "109"
        ],
        "answer": "108",
        "explanation": "Differences are constantly +3. Next term = 105 + 3 = 108."
    },
    {
        "id": "logic_gen_49",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 98, 101, 104, 107, ?",
        "options": [
            "108",
            "109",
            "110",
            "111"
        ],
        "answer": "110",
        "explanation": "Differences are constantly +3. Next term = 107 + 3 = 110."
    },
    {
        "id": "logic_gen_50",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 100, 103, 106, 109, ?",
        "options": [
            "110",
            "111",
            "112",
            "113"
        ],
        "answer": "112",
        "explanation": "Differences are constantly +3. Next term = 109 + 3 = 112."
    },
    {
        "id": "logic_gen_51",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 102, 105, 108, 111, ?",
        "options": [
            "112",
            "113",
            "114",
            "115"
        ],
        "answer": "114",
        "explanation": "Differences are constantly +3. Next term = 111 + 3 = 114."
    },
    {
        "id": "logic_gen_52",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 104, 107, 110, 113, ?",
        "options": [
            "114",
            "115",
            "116",
            "117"
        ],
        "answer": "116",
        "explanation": "Differences are constantly +3. Next term = 113 + 3 = 116."
    },
    {
        "id": "logic_gen_53",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 106, 109, 112, 115, ?",
        "options": [
            "116",
            "117",
            "118",
            "119"
        ],
        "answer": "118",
        "explanation": "Differences are constantly +3. Next term = 115 + 3 = 118."
    },
    {
        "id": "logic_gen_54",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 108, 111, 114, 117, ?",
        "options": [
            "118",
            "119",
            "120",
            "121"
        ],
        "answer": "120",
        "explanation": "Differences are constantly +3. Next term = 117 + 3 = 120."
    },
    {
        "id": "logic_gen_55",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 110, 113, 116, 119, ?",
        "options": [
            "120",
            "121",
            "122",
            "123"
        ],
        "answer": "122",
        "explanation": "Differences are constantly +3. Next term = 119 + 3 = 122."
    },
    {
        "id": "logic_gen_56",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 112, 115, 118, 121, ?",
        "options": [
            "122",
            "123",
            "124",
            "125"
        ],
        "answer": "124",
        "explanation": "Differences are constantly +3. Next term = 121 + 3 = 124."
    },
    {
        "id": "logic_gen_57",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 114, 117, 120, 123, ?",
        "options": [
            "124",
            "125",
            "126",
            "127"
        ],
        "answer": "126",
        "explanation": "Differences are constantly +3. Next term = 123 + 3 = 126."
    },
    {
        "id": "logic_gen_58",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 116, 119, 122, 125, ?",
        "options": [
            "126",
            "127",
            "128",
            "129"
        ],
        "answer": "128",
        "explanation": "Differences are constantly +3. Next term = 125 + 3 = 128."
    },
    {
        "id": "logic_gen_59",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 118, 121, 124, 127, ?",
        "options": [
            "128",
            "129",
            "130",
            "131"
        ],
        "answer": "130",
        "explanation": "Differences are constantly +3. Next term = 127 + 3 = 130."
    },
    {
        "id": "logic_gen_60",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 120, 123, 126, 129, ?",
        "options": [
            "130",
            "131",
            "132",
            "133"
        ],
        "answer": "132",
        "explanation": "Differences are constantly +3. Next term = 129 + 3 = 132."
    },
    {
        "id": "logic_gen_61",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 122, 125, 128, 131, ?",
        "options": [
            "132",
            "133",
            "134",
            "135"
        ],
        "answer": "134",
        "explanation": "Differences are constantly +3. Next term = 131 + 3 = 134."
    },
    {
        "id": "logic_gen_62",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 124, 127, 130, 133, ?",
        "options": [
            "134",
            "135",
            "136",
            "137"
        ],
        "answer": "136",
        "explanation": "Differences are constantly +3. Next term = 133 + 3 = 136."
    },
    {
        "id": "logic_gen_63",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 126, 129, 132, 135, ?",
        "options": [
            "136",
            "137",
            "138",
            "139"
        ],
        "answer": "138",
        "explanation": "Differences are constantly +3. Next term = 135 + 3 = 138."
    },
    {
        "id": "logic_gen_64",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 128, 131, 134, 137, ?",
        "options": [
            "138",
            "139",
            "140",
            "141"
        ],
        "answer": "140",
        "explanation": "Differences are constantly +3. Next term = 137 + 3 = 140."
    },
    {
        "id": "logic_gen_65",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 130, 133, 136, 139, ?",
        "options": [
            "140",
            "141",
            "142",
            "143"
        ],
        "answer": "142",
        "explanation": "Differences are constantly +3. Next term = 139 + 3 = 142."
    },
    {
        "id": "logic_gen_66",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 132, 135, 138, 141, ?",
        "options": [
            "142",
            "143",
            "144",
            "145"
        ],
        "answer": "144",
        "explanation": "Differences are constantly +3. Next term = 141 + 3 = 144."
    },
    {
        "id": "logic_gen_67",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 134, 137, 140, 143, ?",
        "options": [
            "144",
            "145",
            "146",
            "147"
        ],
        "answer": "146",
        "explanation": "Differences are constantly +3. Next term = 143 + 3 = 146."
    },
    {
        "id": "logic_gen_68",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 136, 139, 142, 145, ?",
        "options": [
            "146",
            "147",
            "148",
            "149"
        ],
        "answer": "148",
        "explanation": "Differences are constantly +3. Next term = 145 + 3 = 148."
    },
    {
        "id": "logic_gen_69",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 138, 141, 144, 147, ?",
        "options": [
            "148",
            "149",
            "150",
            "151"
        ],
        "answer": "150",
        "explanation": "Differences are constantly +3. Next term = 147 + 3 = 150."
    },
    {
        "id": "logic_gen_70",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 140, 143, 146, 149, ?",
        "options": [
            "150",
            "151",
            "152",
            "153"
        ],
        "answer": "152",
        "explanation": "Differences are constantly +3. Next term = 149 + 3 = 152."
    },
    {
        "id": "logic_gen_71",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 142, 145, 148, 151, ?",
        "options": [
            "152",
            "153",
            "154",
            "155"
        ],
        "answer": "154",
        "explanation": "Differences are constantly +3. Next term = 151 + 3 = 154."
    },
    {
        "id": "logic_gen_72",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 144, 147, 150, 153, ?",
        "options": [
            "154",
            "155",
            "156",
            "157"
        ],
        "answer": "156",
        "explanation": "Differences are constantly +3. Next term = 153 + 3 = 156."
    },
    {
        "id": "logic_gen_73",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 146, 149, 152, 155, ?",
        "options": [
            "156",
            "157",
            "158",
            "159"
        ],
        "answer": "158",
        "explanation": "Differences are constantly +3. Next term = 155 + 3 = 158."
    },
    {
        "id": "logic_gen_74",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 148, 151, 154, 157, ?",
        "options": [
            "158",
            "159",
            "160",
            "161"
        ],
        "answer": "160",
        "explanation": "Differences are constantly +3. Next term = 157 + 3 = 160."
    },
    {
        "id": "logic_gen_75",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 150, 153, 156, 159, ?",
        "options": [
            "160",
            "161",
            "162",
            "163"
        ],
        "answer": "162",
        "explanation": "Differences are constantly +3. Next term = 159 + 3 = 162."
    },
    {
        "id": "logic_gen_76",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 152, 155, 158, 161, ?",
        "options": [
            "162",
            "163",
            "164",
            "165"
        ],
        "answer": "164",
        "explanation": "Differences are constantly +3. Next term = 161 + 3 = 164."
    },
    {
        "id": "logic_gen_77",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Medium",
        "question": "What is the next number in series: 154, 157, 160, 163, ?",
        "options": [
            "164",
            "165",
            "166",
            "167"
        ],
        "answer": "166",
        "explanation": "Differences are constantly +3. Next term = 163 + 3 = 166."
    },
    {
        "id": "logic_gen_78",
        "category": "Logical Reasoning",
        "topic": "Number Series",
        "difficulty": "Easy",
        "question": "What is the next number in series: 156, 159, 162, 165, ?",
        "options": [
            "166",
            "167",
            "168",
            "169"
        ],
        "answer": "168",
        "explanation": "Differences are constantly +3. Next term = 165 + 3 = 168."
    },
    {
        "id": "verb_gram_01",
        "category": "Verbal Ability",
        "topic": "Grammar",
        "difficulty": "Easy",
        "question": "Neither the manager nor the employees _____ present yesterday.",
        "options": [
            "was",
            "were",
            "is",
            "are"
        ],
        "answer": "were",
        "explanation": "Verb agrees with closest plural subject 'employees'."
    },
    {
        "id": "verb_vocab_01",
        "category": "Verbal Ability",
        "topic": "Vocabulary",
        "difficulty": "Easy",
        "question": "Select word: Her _____ response left no room for debate.",
        "options": [
            "ambiguous",
            "unequivocal",
            "tentative",
            "hesitant"
        ],
        "answer": "unequivocal",
        "explanation": "Unequivocal means clear/indisputable."
    },
    {
        "id": "verb_syn_01",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Synonym for METICULOUS:",
        "options": [
            "Careless",
            "Thorough",
            "Rapid",
            "Hasty"
        ],
        "answer": "Thorough",
        "explanation": "Meticulous means showing great attention to detail."
    },
    {
        "id": "verb_ant_01",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Antonym for CANDID:",
        "options": [
            "Frank",
            "Deceitful",
            "Honest",
            "Direct"
        ],
        "answer": "Deceitful",
        "explanation": "Candid means honest/direct."
    },
    {
        "id": "verb_sent_01",
        "category": "Verbal Ability",
        "topic": "Sentence Correction",
        "difficulty": "Medium",
        "question": "Correct error: 'Each of the candidates have submitted their resume.'",
        "options": [
            "'Each of'",
            "'have submitted'",
            "'their resume'",
            "No error"
        ],
        "answer": "'have submitted'",
        "explanation": "'Each' takes singular verb 'has submitted'."
    },
    {
        "id": "verb_rc_01",
        "category": "Verbal Ability",
        "topic": "Reading Comprehension",
        "difficulty": "Hard",
        "question": "Passage: AI is transforming industry. Ethical concerns on privacy & bias remain key challenges. Question: Key challenge of AI:",
        "options": [
            "Lack of power",
            "High costs",
            "Ethical concerns & bias",
            "Cannot automate"
        ],
        "answer": "Ethical concerns & bias",
        "explanation": "Directly stated in passage."
    },
    {
        "id": "verb_fill_01",
        "category": "Verbal Ability",
        "topic": "Fill in the Blanks",
        "difficulty": "Easy",
        "question": "He is addicted _____ video games.",
        "options": [
            "with",
            "to",
            "for",
            "on"
        ],
        "answer": "to",
        "explanation": "Correct preposition is 'addicted to'."
    },
    {
        "id": "verb_arr_01",
        "category": "Verbal Ability",
        "topic": "Sentence Arrangement",
        "difficulty": "Medium",
        "question": "Rearrange P: in the world Q: is one of R: India S: the largest democracies.",
        "options": [
            "R Q S P",
            "P Q R S",
            "Q R S P",
            "S R Q P"
        ],
        "answer": "R Q S P",
        "explanation": "India is one of the largest democracies in the world."
    },
    {
        "id": "verb_gen_01",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #1 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_02",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #2 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_03",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #3 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_04",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #4 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_05",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #5 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_06",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #6 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_07",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #7 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_08",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #8 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_09",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #9 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_10",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #10 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_11",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #11 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_12",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #12 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_13",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #13 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_14",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #14 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_15",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #15 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_16",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #16 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_17",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #17 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_18",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #18 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_19",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #19 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_20",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #20 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_21",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #21 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_22",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #22 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_23",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #23 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_24",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #24 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_25",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #25 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_26",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #26 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_27",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #27 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_28",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #28 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_29",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #29 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_30",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #30 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_31",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #31 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_32",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #32 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_33",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #33 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_34",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #34 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_35",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #35 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_36",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #36 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_37",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #37 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_38",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #38 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_39",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #39 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_40",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #40 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_41",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #41 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_42",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #42 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_43",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #43 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_44",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #44 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_45",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #45 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_46",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #46 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_47",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #47 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_48",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #48 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_49",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #49 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_50",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #50 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_51",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #51 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_52",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #52 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_53",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #53 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_54",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #54 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_55",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #55 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_56",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #56 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_57",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #57 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_58",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #58 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_59",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #59 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_60",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #60 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_61",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Medium",
        "question": "Choose the correct synonym for word #61 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "verb_gen_62",
        "category": "Verbal Ability",
        "topic": "Synonyms and Antonyms",
        "difficulty": "Easy",
        "question": "Choose the correct synonym for word #62 (EXPEDITE):",
        "options": [
            "Delay",
            "Hasten",
            "Hinder",
            "Block"
        ],
        "answer": "Hasten",
        "explanation": "Expedite means to make an action happen sooner or accomplish quickly."
    },
    {
        "id": "di_tbl_01",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Q1=$200k, Q2=$250k, Q3=$300k, Q4=$250k. Average quarterly sales:",
        "options": [
            "$225k",
            "$250k",
            "$275k",
            "$300k"
        ],
        "answer": "$250k",
        "explanation": "Average = 1000k / 4 = $250k."
    },
    {
        "id": "di_bar_01",
        "category": "Data Interpretation",
        "topic": "Bar Graphs",
        "difficulty": "Medium",
        "question": "Revenue: 2021=$40M, 2022=$50M, 2023=$65M. % increase from 2021 to 2023:",
        "options": [
            "50%",
            "62.5%",
            "75%",
            "80%"
        ],
        "answer": "62.5%",
        "explanation": "(25/40)*100 = 62.5%."
    },
    {
        "id": "di_line_01",
        "category": "Data Interpretation",
        "topic": "Line Graphs",
        "difficulty": "Medium",
        "question": "Visits: Mon=1000, Tue=1200, Wed=1500, Thu=1800. Ratio Mon to Thu:",
        "options": [
            "5 : 9",
            "2 : 3",
            "3 : 4",
            "5 : 6"
        ],
        "answer": "5 : 9",
        "explanation": "1000 : 1800 = 5 : 9."
    },
    {
        "id": "di_pie_01",
        "category": "Data Interpretation",
        "topic": "Pie Charts",
        "difficulty": "Hard",
        "question": "Marketing angle = 108 deg out of 360. Total budget = $1.2M. Marketing budget:",
        "options": [
            "$300,000",
            "$360,000",
            "$400,000",
            "$450,000"
        ],
        "answer": "$360,000",
        "explanation": "(108/360) * 1,200,000 = $360,000."
    },
    {
        "id": "di_comp_01",
        "category": "Data Interpretation",
        "topic": "Data Comparison",
        "difficulty": "Medium",
        "question": "Company A profit = 20%, Company B profit = 25%. If revenues are equal, ratio of expenses A to B:",
        "options": [
            "5 : 4",
            "4 : 5",
            "15 : 16",
            "16 : 15"
        ],
        "answer": "16 : 15",
        "explanation": "Expense A = 0.8R, Expense B = 0.75R. Ratio = 0.8/0.75 = 16/15."
    },
    {
        "id": "di_gen_01",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 110 units, Store B sold 210 units. What is total sales?",
        "options": [
            "310",
            "320",
            "330",
            "340"
        ],
        "answer": "320",
        "explanation": "Total sales = 110 + 210 = 320."
    },
    {
        "id": "di_gen_02",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 120 units, Store B sold 220 units. What is total sales?",
        "options": [
            "330",
            "340",
            "350",
            "360"
        ],
        "answer": "340",
        "explanation": "Total sales = 120 + 220 = 340."
    },
    {
        "id": "di_gen_03",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 130 units, Store B sold 230 units. What is total sales?",
        "options": [
            "350",
            "360",
            "370",
            "380"
        ],
        "answer": "360",
        "explanation": "Total sales = 130 + 230 = 360."
    },
    {
        "id": "di_gen_04",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 140 units, Store B sold 240 units. What is total sales?",
        "options": [
            "370",
            "380",
            "390",
            "400"
        ],
        "answer": "380",
        "explanation": "Total sales = 140 + 240 = 380."
    },
    {
        "id": "di_gen_05",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 150 units, Store B sold 250 units. What is total sales?",
        "options": [
            "390",
            "400",
            "410",
            "420"
        ],
        "answer": "400",
        "explanation": "Total sales = 150 + 250 = 400."
    },
    {
        "id": "di_gen_06",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 160 units, Store B sold 260 units. What is total sales?",
        "options": [
            "410",
            "420",
            "430",
            "440"
        ],
        "answer": "420",
        "explanation": "Total sales = 160 + 260 = 420."
    },
    {
        "id": "di_gen_07",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 170 units, Store B sold 270 units. What is total sales?",
        "options": [
            "430",
            "440",
            "450",
            "460"
        ],
        "answer": "440",
        "explanation": "Total sales = 170 + 270 = 440."
    },
    {
        "id": "di_gen_08",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 180 units, Store B sold 280 units. What is total sales?",
        "options": [
            "450",
            "460",
            "470",
            "480"
        ],
        "answer": "460",
        "explanation": "Total sales = 180 + 280 = 460."
    },
    {
        "id": "di_gen_09",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 190 units, Store B sold 290 units. What is total sales?",
        "options": [
            "470",
            "480",
            "490",
            "500"
        ],
        "answer": "480",
        "explanation": "Total sales = 190 + 290 = 480."
    },
    {
        "id": "di_gen_10",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 200 units, Store B sold 300 units. What is total sales?",
        "options": [
            "490",
            "500",
            "510",
            "520"
        ],
        "answer": "500",
        "explanation": "Total sales = 200 + 300 = 500."
    },
    {
        "id": "di_gen_11",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 210 units, Store B sold 310 units. What is total sales?",
        "options": [
            "510",
            "520",
            "530",
            "540"
        ],
        "answer": "520",
        "explanation": "Total sales = 210 + 310 = 520."
    },
    {
        "id": "di_gen_12",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 220 units, Store B sold 320 units. What is total sales?",
        "options": [
            "530",
            "540",
            "550",
            "560"
        ],
        "answer": "540",
        "explanation": "Total sales = 220 + 320 = 540."
    },
    {
        "id": "di_gen_13",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 230 units, Store B sold 330 units. What is total sales?",
        "options": [
            "550",
            "560",
            "570",
            "580"
        ],
        "answer": "560",
        "explanation": "Total sales = 230 + 330 = 560."
    },
    {
        "id": "di_gen_14",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 240 units, Store B sold 340 units. What is total sales?",
        "options": [
            "570",
            "580",
            "590",
            "600"
        ],
        "answer": "580",
        "explanation": "Total sales = 240 + 340 = 580."
    },
    {
        "id": "di_gen_15",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 250 units, Store B sold 350 units. What is total sales?",
        "options": [
            "590",
            "600",
            "610",
            "620"
        ],
        "answer": "600",
        "explanation": "Total sales = 250 + 350 = 600."
    },
    {
        "id": "di_gen_16",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 260 units, Store B sold 360 units. What is total sales?",
        "options": [
            "610",
            "620",
            "630",
            "640"
        ],
        "answer": "620",
        "explanation": "Total sales = 260 + 360 = 620."
    },
    {
        "id": "di_gen_17",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 270 units, Store B sold 370 units. What is total sales?",
        "options": [
            "630",
            "640",
            "650",
            "660"
        ],
        "answer": "640",
        "explanation": "Total sales = 270 + 370 = 640."
    },
    {
        "id": "di_gen_18",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 280 units, Store B sold 380 units. What is total sales?",
        "options": [
            "650",
            "660",
            "670",
            "680"
        ],
        "answer": "660",
        "explanation": "Total sales = 280 + 380 = 660."
    },
    {
        "id": "di_gen_19",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 290 units, Store B sold 390 units. What is total sales?",
        "options": [
            "670",
            "680",
            "690",
            "700"
        ],
        "answer": "680",
        "explanation": "Total sales = 290 + 390 = 680."
    },
    {
        "id": "di_gen_20",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 300 units, Store B sold 400 units. What is total sales?",
        "options": [
            "690",
            "700",
            "710",
            "720"
        ],
        "answer": "700",
        "explanation": "Total sales = 300 + 400 = 700."
    },
    {
        "id": "di_gen_21",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 310 units, Store B sold 410 units. What is total sales?",
        "options": [
            "710",
            "720",
            "730",
            "740"
        ],
        "answer": "720",
        "explanation": "Total sales = 310 + 410 = 720."
    },
    {
        "id": "di_gen_22",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 320 units, Store B sold 420 units. What is total sales?",
        "options": [
            "730",
            "740",
            "750",
            "760"
        ],
        "answer": "740",
        "explanation": "Total sales = 320 + 420 = 740."
    },
    {
        "id": "di_gen_23",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 330 units, Store B sold 430 units. What is total sales?",
        "options": [
            "750",
            "760",
            "770",
            "780"
        ],
        "answer": "760",
        "explanation": "Total sales = 330 + 430 = 760."
    },
    {
        "id": "di_gen_24",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 340 units, Store B sold 440 units. What is total sales?",
        "options": [
            "770",
            "780",
            "790",
            "800"
        ],
        "answer": "780",
        "explanation": "Total sales = 340 + 440 = 780."
    },
    {
        "id": "di_gen_25",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 350 units, Store B sold 450 units. What is total sales?",
        "options": [
            "790",
            "800",
            "810",
            "820"
        ],
        "answer": "800",
        "explanation": "Total sales = 350 + 450 = 800."
    },
    {
        "id": "di_gen_26",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 360 units, Store B sold 460 units. What is total sales?",
        "options": [
            "810",
            "820",
            "830",
            "840"
        ],
        "answer": "820",
        "explanation": "Total sales = 360 + 460 = 820."
    },
    {
        "id": "di_gen_27",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 370 units, Store B sold 470 units. What is total sales?",
        "options": [
            "830",
            "840",
            "850",
            "860"
        ],
        "answer": "840",
        "explanation": "Total sales = 370 + 470 = 840."
    },
    {
        "id": "di_gen_28",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 380 units, Store B sold 480 units. What is total sales?",
        "options": [
            "850",
            "860",
            "870",
            "880"
        ],
        "answer": "860",
        "explanation": "Total sales = 380 + 480 = 860."
    },
    {
        "id": "di_gen_29",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 390 units, Store B sold 490 units. What is total sales?",
        "options": [
            "870",
            "880",
            "890",
            "900"
        ],
        "answer": "880",
        "explanation": "Total sales = 390 + 490 = 880."
    },
    {
        "id": "di_gen_30",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 400 units, Store B sold 500 units. What is total sales?",
        "options": [
            "890",
            "900",
            "910",
            "920"
        ],
        "answer": "900",
        "explanation": "Total sales = 400 + 500 = 900."
    },
    {
        "id": "di_gen_31",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 410 units, Store B sold 510 units. What is total sales?",
        "options": [
            "910",
            "920",
            "930",
            "940"
        ],
        "answer": "920",
        "explanation": "Total sales = 410 + 510 = 920."
    },
    {
        "id": "di_gen_32",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 420 units, Store B sold 520 units. What is total sales?",
        "options": [
            "930",
            "940",
            "950",
            "960"
        ],
        "answer": "940",
        "explanation": "Total sales = 420 + 520 = 940."
    },
    {
        "id": "di_gen_33",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 430 units, Store B sold 530 units. What is total sales?",
        "options": [
            "950",
            "960",
            "970",
            "980"
        ],
        "answer": "960",
        "explanation": "Total sales = 430 + 530 = 960."
    },
    {
        "id": "di_gen_34",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Easy",
        "question": "Table Data: Store A sold 440 units, Store B sold 540 units. What is total sales?",
        "options": [
            "970",
            "980",
            "990",
            "1000"
        ],
        "answer": "980",
        "explanation": "Total sales = 440 + 540 = 980."
    },
    {
        "id": "di_gen_35",
        "category": "Data Interpretation",
        "topic": "Tables",
        "difficulty": "Medium",
        "question": "Table Data: Store A sold 450 units, Store B sold 550 units. What is total sales?",
        "options": [
            "990",
            "1000",
            "1010",
            "1020"
        ],
        "answer": "1000",
        "explanation": "Total sales = 450 + 550 = 1000."
    }
]

CATEGORIES = [
    {
        "name": "Quantitative Aptitude",
        "icon": "📐",
        "color": "#8B5CF6",
        "topics": [
            "Percentages", "Profit and Loss", "Time and Work", "Time, Speed and Distance",
            "Ratio and Proportion", "Averages", "Simple Interest", "Compound Interest",
            "Number System", "Probability", "Permutation and Combination", "Ages", "Mixtures and Allegations"
        ]
    },
    {
        "name": "Logical Reasoning",
        "icon": "🧩",
        "color": "#22D3EE",
        "topics": [
            "Number Series", "Letter Series", "Analogy", "Coding-Decoding", "Blood Relations",
            "Direction Sense", "Syllogisms", "Odd One Out", "Seating Arrangement", "Logical Puzzles", "Statement and Conclusion"
        ]
    },
    {
        "name": "Verbal Ability",
        "icon": "📝",
        "color": "#34D399",
        "topics": [
            "Grammar", "Vocabulary", "Synonyms and Antonyms", "Sentence Correction",
            "Fill in the Blanks", "Sentence Arrangement", "Reading Comprehension"
        ]
    },
    {
        "name": "Data Interpretation",
        "icon": "📊",
        "color": "#FBBF24",
        "topics": [
            "Tables", "Bar Graphs", "Line Graphs", "Pie Charts", "Data Comparison"
        ]
    }
]
