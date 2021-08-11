import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


def create_question(question_text, days):
    """
    Create a question with the given ´question_text´ and published the
    given number of ´days´ offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choice(question, choice_text="Default Choice"):
    """
    Create a Choice bond to the given question
    """
    return Choice.objects.create(question=question, choice_text=choice_text)


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for
        questions whose pub_date is in the future
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for
        questions whose pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for 
        questions whose pub_date is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """If no questions exist, an appropriate message is displayed."""
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_questions_without_choices(self):
        """
        Questions that does not have choices aren't displayed on the index page.
        """
        question = create_question(
            question_text="Question without choices.", days=-30
        )
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")

    def test_questions_with_choices(self):
        """
        Questions with one or more choices are displayed on the index page.
        """
        question = create_question(
            question_text="Question with two choices.", days=-30
        )
        create_choice(question=question)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question],
        )

    def test_past_question(self):
        """Questions with a pub date in the past are displayed on the index page."""
        question = create_question(question_text="Past Question.", days=-30)
        create_choice(question=question)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date on in the future aren't displayed on the index page.
        """
        question = create_question(question_text="Future Question.", days=30)
        create_choice(question=question)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")

    def test_future_question_and_past_question(self):
        """
        Even if both past and future question exist, only past ones are displayed.
        """
        past_question = create_question(question_text="Past Question.", days=-30)
        future_question = create_question(question_text="Future Question.", days=30)

        create_choice(question=past_question)
        create_choice(question=future_question)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [past_question]
        )

    def test_two_past_questions(self):
        """The questions index page may display multiple questions."""
        question1 = create_question(question_text="Past Question 1.", days=-30)
        question2 = create_question(question_text="Past Question 2.", days=-5)

        create_choice(question=question1)
        create_choice(question=question2)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context["latest_question_list"], [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_question_without_choices(self):
        """The detail view of a question without choices returns a 404 not found."""
        question = create_question(question_text="Question Without Choices.", days=-5)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_question_with_choices(self):
        """
        The detail view of a question with one or more choices displays
        the question's tex and the choices text.
        """
        question = create_question(
            question_text="Question With Choices.", days=-5
        )
        choice = create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)

        self.assertContains(response, question.question_text)
        self.assertContains(response, choice.choice_text)

    def test_future_question(self):
        """
        The detail view of a question with a pub_date
        in the future returns a 404 not found.
        """
        question = create_question(question_text="Future Question.", days=30)
        create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text and the choices text
        """
        question = create_question(question_text="Past Question.", days=-30)
        create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertContains(response, question.question_text)

        for choice in question.choice_set.all():
            self.assertContains(response, choice.choice_text)


class QuestionResultsDetailViewTests(TestCase):
    def test_questions_without_choices(self):
        """
        The results view of a question without choices
        returns a 404 not found.
        """
        question = create_question(question_text="Question without choices.", days=-30)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_question_with_choices(self):
        """
        The results view of a question with one or more choices
        displays the question's text.
        """
        question = create_question(
            question_text="Question with choices", days=-30
        )
        choice = create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertContains(response, question.question_text)
        self.assertContains(response, choice.choice_text)

    def test_future_question(self):
        """
        The results view of a question with a pub_date in
        the future returns a 404 not found.
        """
        question = create_question(question_text="Future Question.", days=30)
        create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The results view of a question with a pub_date in the
        past displays the question's text
        """
        question = create_question(question_text="Past Question.", days=-30)
        create_choice(question=question)
        url = reverse('polls:detail', args=(question.id,))
        response = self.client.get(url)
        self.assertContains(response, question.question_text)

