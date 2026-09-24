from io import BytesIO
import unittest
from pypdf import PdfReader
from modules.kabutar_assistant_exports import export_attempt

def sample_attempt():
    formulas=[r'\frac{x^2+1}{\sqrt{\frac{2}{3}}}',r'\displaystyle\cfrac{1}{1+\cfrac{1}{2}}',
              r'\begin{pmatrix}1&2\\3&4\end{pmatrix}',r'\begin{aligned}x+y&=2\\x-y&=0\end{aligned}',
              r'\begin{cases}x^2&x>0\\0&x\leq0\end{cases}',r'\sum_{i=1}^{n}i^2',r'0{,}0001=10^{-4}']
    questions=[]
    for i,formula in enumerate(formulas):
        questions.append({'id':i+1,'question':f'{i+1}-maktab oʻquvchisi uchun misol. [lat]{formula}[/lat] ifodani hisoblang.',
                          'option_a':'[lat]0,0001[/lat]','option_b':r'[lat]\frac{1}{2}[/lat]',
                          'option_c':'[ru]Третий вариант[/ru]','option_d':'[en]Fourth answer[/en]',
                          'correct_answer':'B','points':1,'topic_code':'sample'})
    return {'attempt_id':'rev64-sample','plan':{'grade':'7','minutes':30,'mode':'practice','topics':[{'topic_code':'sample','title':'Formulalar','subject_name':'Matematika'}]},'questions':questions}

class AssistantPdfTests(unittest.TestCase):
    def test_question_paper_has_rendered_formulas_all_questions_and_no_answer_key(self):
        data,kind,name=export_attempt(sample_attempt(),'pdf',False)
        self.assertTrue(data.startswith(b'%PDF-'));self.assertEqual(kind,'application/pdf')
        pdf=PdfReader(BytesIO(data));text=' '.join(page.extract_text() for page in pdf.pages)
        for i in range(1,8):self.assertIn(f'{i}-savol',text)
        self.assertNotIn('Javoblar kaliti',text);self.assertNotIn('[lat]',text);self.assertNotIn('\\frac',text)
        self.assertTrue(sum(len(page.images) for page in pdf.pages)>=7)

    def test_answer_key_is_separate_and_question_payload_is_unchanged(self):
        attempt=sample_attempt();original=attempt['questions'][0]['question']
        data,_,_=export_attempt(attempt,'pdf',True)
        text=' '.join(page.extract_text() for page in PdfReader(BytesIO(data)).pages)
        self.assertIn('Javoblar kaliti',text);self.assertEqual(attempt['questions'][0]['question'],original)

if __name__=='__main__':unittest.main()
