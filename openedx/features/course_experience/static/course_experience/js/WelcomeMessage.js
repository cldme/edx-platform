/* globals $ */
import 'jquery.cookie';
import { clampHtmlByWords } from 'common/js/utils/clamp-html';

export class WelcomeMessage {  // eslint-disable-line import/prefer-default-export

  static dismissWelcomeMessage(dismissUrl) {
    $.ajax({
      type: 'POST',
      url: dismissUrl,
      headers: {
        'X-CSRFToken': $.cookie('csrftoken'),
      },
      success: () => {
        $('.welcsavepointome-message').hide();
      },
    });
  }

  constructor(options) {
    // Dismiss the welcome message if the user clicks dismiss, or auto-dismiss if
    // the user doesn't click dismiss in 7 days from when it was first viewed.

    // Check to see if the welcome message has been displayed at all.
    if ($('.welcome-message').length > 0) {
      // If the welcome message has been viewed.
      if ($.cookie('welcome-message-viewed') === 'True') {
        // If the timer cookie no longer exists, dismiss the welcome message permanently.
        if ($.cookie('welcome-message-timer') !== 'True') {
          WelcomeMessage.dismissWelcomeMessage(options.dismissUrl);
        }
      } else {
        // Set both the viewed cookie and the timer cookie.
        $.cookie('welcome-message-viewed', 'True', { expires: 365 });
        $.cookie('welcome-message-timer', 'True', { expires: 7 });
      }
    }
    $('.dismiss-message button').click(() => WelcomeMessage.dismissWelcomeMessage(options.dismissUrl));


    // "Show More" support for welcome messages (i.e. the update message)
    const welcomeMessage = document.querySelector('.welcome-message-content');
    const longMessage = welcomeMessage.cloneNode(true);
      clampHtmlByWords(welcomeMessage, 100);
    console.log('MIKE:', longMessage);
    const showMoreButton = document.querySelector('#welcome-message-show-more');
    $('.welcome-message .welcome-message-show-more').click((event) => {
        console.log("MIKE: clicked", event);

      // const toggleAllExpanded = toggleAllButton.getAttribute('aria-expanded') === 'true';
      // let sectionAction;
      // /* globals gettext */
      // if (toggleAllExpanded) {
      //   toggleAllButton.setAttribute('aria-expanded', 'false');
      //   sectionAction = collapseSection;
      //   toggleAllSpan.classList.add(extraPaddingClass);
      //   toggleAllSpan.innerText = gettext('Expand All');
      // } else {
      //   toggleAllButton.setAttribute('aria-expanded', 'true');
      //   sectionAction = expandSection;
      //   toggleAllSpan.classList.remove(extraPaddingClass);
      //   toggleAllSpan.innerText = gettext('Collapse All');
      // }
      // const sections = Array.prototype.slice.call(document.querySelectorAll('.accordion-trigger'));
      // sections.forEach((sectionToggleButton) => {
      //   sectionAction(sectionToggleButton);
      // });
      event.stopImmediatePropagation();
    });

  }
}
