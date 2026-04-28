import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # use beautifulsoup or lxml to get content
    # ignore stop words

    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # resource: https://www.geeksforgeeks.org/python/beautifulsoup-scraping-link-from-html/
    found_urls = []

    # checking to make sure there was no error
    if resp.status != 200:
        print(resp.error)
        return found_urls
    
    # checking to make sure there is a page and content
    if not resp.raw_response:
        return found_urls
    if not resp.raw_response.content:
        return found_urls
    
    # checking to make sure the content is text/html
    content_type = resp.raw_response.headers.get("content-type", "")
    if "text/html" not in content_type:
        return found_urls
    
    content = BeautifulSoup(resp.raw_response.content, 'lxml')
    for tag in content.find_all("a", href=True):
        new_url = tag["href"]
        try:
            new_url = urljoin(url, new_url)
        except ValueError:
            continue
        new_url = new_url.split("#")[0]
        if new_url:
            found_urls.append(new_url)


    return found_urls

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # REASONS URL IS INVALID:
        # invalid extensions- not pointing to a webpage
        # potential trap - example: ics calendar which will be infinite
        # webpage is NOT a subdomain of *.ics.uci.edu/*, *.cs.uci.edu/*, *.informatics.uci.edu/*, or *.stat.uci.edu/*
        # scheme is not http or https

    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False
        # make sure domain is valid
        valid_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
        if not any(parsed.netloc == domain or parsed.netloc.endswith("." + domain) for domain in valid_domains):
            return False
        # avoid date traps
        if re.search(r"\d{4}-\d{2}-\d{2}", parsed.query.lower()) or \
            re.search(r"(month|year|day)=\d+", parsed.query.lower()):
            return False
        # avoid page traps
        if re.search(r"/page/\d+(-\d+)?(/|$)", parsed.path):
            return False
        # Avoiding date traps ALSO IN THE PATH
        if re.search(r"\d{4}-\d{2}-\d{2}", parsed.path.lower()) or \
            re.search(r"\d{2}-\d{2}-\d{4}", parsed.path.lower()) or \
            re.search(r"\d{4}-\d{2}", parsed.path.lower()) or \
            re.search(r"\d{4}-", parsed.path.lower()) or \
            re.search(r"-\d{4}", parsed.path.lower()):
            return False
        # Avoiding doku.php (which seemed to be a crawler trap)
        if "doku.php" in parsed.path:
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|ics"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def main():
    testurls = ["https://courselisting.ics.uci.edu/ugrad_courses/",
               "https://www.ics.uci.edu/",
                "https://www.cs.uci.edu/grad/",
                "https://www.informatics.uci.edu/about/",
                "https://www.stat.uci.edu/seminars/",
                "https://www.ics.uci.edu/page#section",
                "https://www.ics.uci.edu/image.png", # bad extension
                "https://google.com/", # wrong domain
                "ftp://www.ics.uci.edu/", # bad schema
                "https://ics.uci.edu/events/list/?tribe-bar-date=2026-05-16"] # date trap
    for url in testurls:
        print(is_valid(url))

    test_content = "<p>You can find the landing pages for the Engineering and Merage teaching plans at the following links: <ul><li><a href='https://merage.uci.edu/programs/undergraduate/enrollment.html' target='blank'>Merage Academic Year Teaching Plan</a></li><li><a href='https://undergraduate.eng.uci.edu/teaching-plan/'  target='blank'>Engineering Academic Year Teaching Plan</a></li></ul><p />"


# if __name__ == "__main__":
#     main()