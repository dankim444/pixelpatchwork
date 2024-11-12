#Project Overview

Our project will begin by redirecting workers to a site we have set up. In the beginning of the day the site will have a starting image along with a request asking the workers to give a prompt to update the image. This request could be something along the lines of "Write a prompt to make this image funnier." Once the worker gives a request for a change to this image we use gpt image generation to make that change. We then store this images. In the second half of the day we then show all the images generated for the day and ask users to vote on which image they like the most. This will then lead to a final image that wins. This final image will then be the starting image for the next day. By the end of the experiment we will have a list of winning images along with an end image which is the result of all the days of aggregation.

#Project flow
Our design flow can be found in the Nets2130Flow.drawio.png file

We start with the starting image. The workers then give a suggestion to change the image. An ai generated image is then put into an image dataset. Then these images are then brought back to the workers to vote on. Finally the final image is sent back to the start of the flow for the next day. 


