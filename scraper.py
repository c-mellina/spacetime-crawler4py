import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import analytics
from dup_detector import ExactDetector, NearDetector

# detectors persist across all pages 
exact_detector = ExactDetector()
near_detector = NearDetector(0.95)

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
    stop_words = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an",
        "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
        "before", "being", "below", "between", "both", "but", "by", "can't",
        "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
        "doing", "don't", "down", "during", "each", "few", "for", "from",
        "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
        "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers",
        "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
        "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
        "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
        "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
        "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
        "such", "than", "that", "that's", "the", "their", "theirs", "them",
        "themselves", "then", "there", "there's", "these", "they", "they'd",
        "they'll", "they're", "they've", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
        "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
        "where", "where's", "which", "while", "who", "who's", "whom", "why",
        "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
        "you're", "you've", "your", "yours", "yourself", "yourselves"
        }

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
    if "text/html" not in content_type.lower():
        return found_urls
    
    # Check the HTTP response header to ensure the dataset is not too large
    content_length = resp.raw_response.headers.get("content-length", "")
    if content_length:
        try:
            if int(content_length) > 1000000:    # We can change this threshold as seen fit (it is currently 1 million)
                return found_urls
        except ValueError:
            pass
    
    # get next URLs
    content = BeautifulSoup(resp.raw_response.content, 'lxml')
    for tag in content.find_all("a", href=True):
        href = tag["href"].strip()
 
        # skip non-page links
        if href == "" or href.startswith("#"):
            continue
        if href.lower().startswith("javascript:"):
            continue
        if href.lower().startswith("mailto:"):
            continue
        if href.lower().startswith("tel:"):
            continue
 
        try:
            new_url = urljoin(url, href)
        except ValueError:
            continue
            
        new_url = urldefrag(new_url).url
 
        if new_url:
            found_urls.append(new_url)

    #remove script tags so dont count as words
    for tag in content(["script", "style"]):
        tag.decompose()

    # parse text and ignore stop words
    text = content.get_text()
    words = re.split(r'\W+', text.lower())
    words = [w for w in words if w and len(w) > 1 and w not in stop_words and not w.isnumeric()]

    # returning if there were no words
    if not words:
        return found_urls
    # Tentative exact duplicate detection
    if exact_detector.is_exact_duplicate(words):
        return []
    
    if near_detector.is_near_duplicate(words):
        return []

    #update all analytics including subdomain count
    analytics.add_page(urldefrag(resp.url).url, words)

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
        if re.search(r"/page/\d+(-\d+)?/?$", parsed.path.lower()):
            return False
        # Avoiding date traps ALSO IN THE PATH
        if re.search(r"\d{4}-\d{2}-\d{2}", parsed.path.lower()) or \
            re.search(r"\d{2}-\d{2}-\d{4}", parsed.path.lower()) or \
            re.search(r"\d{4}-\d{2}", parsed.path.lower()):
                return False
        # Avoiding b/c seemed to be a crawler trap
        if "doku.php" in parsed.path:
            return False
        if "/events/" in parsed.path.lower() and parsed.query:
            return False
        # query traps
        if parsed.query:
            query = parsed.query.lower()
            if any(x in query for x in [
                "tribe",
                "ical",
                "eventdisplay"
            ]):
                return False
        # avoiding some unneccessary sites it spent a lot of time on
        if ("~dechter/softwares/" in parsed.path) or ("~dechter/courses/" in parsed.path):
            return False
        if "~baldig/learning/" in parsed.path:
            return False
        if "~hziv/ooad/classes/sld" in parsed.path:
            return False
        if "~wscacchi/presentations/" in parsed.path.lower():
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|ics"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|can)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def main():
    testurls = ["https://ics.uci.edu/~dechter/softwares/", # False
                "https://ics.uci.edu/~dechter/courses/", # False
                "https://ics.uci.edu/~baldig/learning/", # False
                "https://ics.uci.edu/~hziv/ooad/classes/sld001.htm", # False
                "https://ics.uci.edu/~wscacchi/Presentations/GameLab/", #False
                "https://courselisting.ics.uci.edu/ugrad_courses/",
                "https://www.ics.uci.edu/",
                "https://www.cs.uci.edu/grad/",
                "https://www.informatics.uci.edu/about/",
                "https://www.stat.uci.edu/seminars/",
                "https://www.ics.uci.edu/page#section",
                "https://www.ics.uci.edu/image.png", # False, bad extension
                "https://google.com/", # False, wrong domain
                "ftp://www.ics.uci.edu/", # False, bad schema
                "https://ics.uci.edu/events/list/?tribe-bar-date=2026-05-16", # False, date trap
                "https://isg.ics.uci.edu/events/tag/talk/list/?eventDisplay=past",#false
                "https://ics.uci.edu/event/hci-for-agi/?ical=1", #false
                "http://ngs.ics.uci.edu/research/projects",
                "https://wics.ics.uci.edu/contact",]
    for url in testurls:
        print(is_valid(url))

    test_content = "<p>You can find the landing pages for the Engineering and Merage teaching plans at the following links: <ul><li><a href='https://merage.uci.edu/programs/undergraduate/enrollment.html' target='blank'>Merage Academic Year Teaching Plan</a></li><li><a href='https://undergraduate.eng.uci.edu/teaching-plan/'  target='blank'>Engineering Academic Year Teaching Plan</a></li></ul><p />"


if __name__ == "__main__":
    main()