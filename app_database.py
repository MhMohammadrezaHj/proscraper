import random
import peewee
import string
import os

from database_manager import DatabaseManager
import local_settings


# connect to postgresql database
database_manager = DatabaseManager(
    database_name=local_settings.DATABASE["name"],
    user=local_settings.DATABASE["user"],
    password=local_settings.DATABASE["password"],
    host=local_settings.DATABASE["host"],
    port=local_settings.DATABASE["port"],
)


def trim_url_slash(url):
    if url[-1] == "/":
        return url[:-1]
    return url


# create a base model for using peewee as an orm
class BaseModel(peewee.Model):
    class Meta:
        database = database_manager.db


class Category(BaseModel):
    TYPE_CHOICES = (
        ("c", "Category"),
        ("l", "Label"),
        ("e", "Event"),
    )
    type = peewee.CharField(max_length=1, choices=TYPE_CHOICES)
    # title = peewee.CharField(max_length=255, null=False)
    slug = peewee.CharField(max_length=255, null=False)


class Author(BaseModel):
    name = peewee.CharField(max_length=155)
    slug = peewee.CharField(max_length=255)


# class ArticleType(BaseModel):
#     TYPE_CHOICES = (
#         ("c", "Category"),
#         ("l", "Label"),
#         ("e", "Event"),
#     )
#     type = peewee.CharField(max_length=1, choices=TYPE_CHOICES)


class Article(BaseModel):
    # type = peewee.ForeignKeyField(ArticleType, backref="articles")
    author = peewee.ForeignKeyField(Author, backref="articles")
    category = peewee.ForeignKeyField(Category, backref="articles")
    title = peewee.CharField(max_length=255, null=False)
    slug = peewee.CharField(max_length=255, null=False)
    year = peewee.SmallIntegerField()
    month = peewee.SmallIntegerField()
    day = peewee.SmallIntegerField()
    # scarping_html_backup_name = peewee.CharField(max_length=1000, null=True)

    def get_full_url(self):
        #        https://techcrunch.com/2024/04/17/dark-space-is-building-a-rocket-powered-boxing-glove-to-push-debris-out-of-orbit/
        return f"https://techcrunch.com/{self.year}/{self.month:02}/{self.day:02}/{self.slug}/"

    def set_year_month_day_slug_from_full_url(self, article_full_url: str):
        # https://techcrunch.com/2024/04/17/dark-space-is-building-a-rocket-powered-boxing-glove-to-push-debris-out-of-orbit/
        article_full_url = article_full_url.replace("https://techcrunch.com/", "")
        if article_full_url[-1] == "/":
            article_full_url = article_full_url[:-1]
        url_split = article_full_url.split("/")
        self.year, self.month, self.day, self.slug = (
            int(url_split[-4]),
            int(url_split[-3]),
            int(url_split[-2]),
            url_split[-1],
        )

    def set_title(self, title):
        self.title = title

    def set_author(self, author_name, author_full_url):
        author_slug = author_full_url.split("/")[-1]

        try:
            self.author = Author.select().where(Author.slug == author_slug).get()
        except peewee.DoesNotExist:
            self.author = Author.create(
                name=author_name,
                slug=author_slug,
            )

    # def set_scarping_html_backup_name(self, html_backup_name):
    #     self.scarping_html_backup_name = html_backup_name

    # def set_type(self, type_full_url=None):  # type: category, label, event
    #     # https://techcrunch.com/events/tc-early-stage-2024/
    #     if type_full_url:
    #         if type_full_url[-1] == "/":
    #             type_full_url = type_full_url[:-1]
    #         type_slug = type_full_url.split("/")[-2]
    #         if type_slug == "events":
    #             type = "e"
    #         elif type_slug == "category":
    #             type = "c"
    #     else:
    #         type = "l"

    #     try:
    #         self.type = ArticleType.select().where(ArticleType.type == type).get()
    #     except peewee.DoesNotExist:
    #         self.type = ArticleType.create(
    #             type=type,
    #         )

    def set_category(self, category_url):
        if category_url:
            if "/category/" in category_url:
                category_slug = category_url.split("/")[-1]
                type = "c"
            elif "/events/" in category_url:
                category_slug = category_url.split("/")[-1]
                type = "e"
        else:
            category_slug = "featured"
            type = "l"

        try:
            self.category = (
                Category.select().where(Category.slug == category_slug).get()
            )
        except peewee.DoesNotExist:
            self.category = Category.create(
                slug=category_slug,
                type=type,
            )

    @staticmethod
    def article_already_exists_check_by_full_url(article_full_url):
        if article_full_url[-1] == "/":
            article_full_url = article_full_url[:-1]
        article_slug = article_full_url.split("/")[-1]
        if Article.select().where(Article.slug == article_slug).exists():
            print("duplicate article")
            return True
        return False


database_manager.create_tables(models=[Category, Author, Article])


def save_article_data_to_database(
    article_full_url,
    author_full_name,
    author_full_url,
    category_full_url,
    article_title,
):
    article_full_url = trim_url_slash(article_full_url)
    author_full_url = trim_url_slash(author_full_url)
    if category_full_url:
        category_full_url = trim_url_slash(category_full_url)
    author_full_name = author_full_name.lower()
    article_title = article_title.lower()

    if not Article.article_already_exists_check_by_full_url(article_full_url):
        article = Article()
        article.set_year_month_day_slug_from_full_url(article_full_url)
        article.set_author(author_full_name, author_full_url)
        article.set_category(category_full_url)
        article.set_title(article_title)
        # article.set_scarping_html_backup_name(html_backup_name)
        article.save()
        return article

    print('duplicate')
    return None


if __name__ == "__main__":

    article_full_url = trim_url_slash(
        "https://techcrunch.com/2024/04/17/dark-space-is-building-a-rocket-powered-boxing-glove-to-push-debris-out-of-orbit/"
    )
    author_full_url = trim_url_slash("https://techcrunch.com/author/aria-alamalhodaei/")
    # type_url = trim_url_slash("https://techcrunch.com/events/tc-early-stage-2024/")
    category_url = trim_url_slash("https://techcrunch.com/category/startups/")
    author_full_name = "firstn".lower()
    title = "sometitle".lower()
    article = Article()
    article.set_year_month_day_slug_from_full_url(article_full_url)
    article.set_author(author_full_name, author_full_url)
    # article.set_type(type_url)
    article.set_title(title)
    article.set_category(category_url)
    # if not article.already_exists():
    article.save()
