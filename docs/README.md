# Project Overview

Our project will begin by redirecting workers to a site we have set up. In the beginning of the day the site will have a starting image along with a request asking the workers to give a prompt to update the image. This request could be something along the lines of "Write a prompt to make this image funnier." Once the worker gives a request for a change to this image we use gpt image generation to make that change. We then store this image (possibly in local storage). In the second half of the workflow, we then show the user all the images generated for the day and ask the user to vote on which image they like the most. This will then lead to a final image that wins. This final image will then be the starting image for the next day. By the end of the experiment we will have a list of winning images along with an end image which is the result of all the days of aggregation.

# Project flow

Our design flow can be found in the Nets2130Flow.drawio.png file

We start with a starting image, corresponding to the most voted-on image from the previous day. If it is day 0, we give the user a random image. The workers then give a suggestion to change the image via a text prompt, which is sent to the image model. The "improved" ai generated image is then put into an image dataset. Then all the images from that day are brought back to the workers to vote on. Finally, the final image is sent back to the start of the flow for the next day.

# Major Components

QC Module: 5 points

- Ensure that all user-submitted prompts and AI-generated images align with the project's goals.
- Flag inappropriate prompts.
- Voting system for choosing best change to make.

Aggregation Module: 5 points

- Compile crowd contributions and determine the "winning" image of the day based on voting results, creating a single image that best represents the collective effort.
- Potentially using weighted voting for users who consistently participate or give prompts that lead to popular images.

Image Generation Module: 3 points

- Generated updated images based on user prompts.

UI: 5 points
Home page-

- Display current image
- Include instructions
- Prompt submission

Voting page-

- Display gallery of generated changes and allow users to vote on their favorites.

Results/History

- See the current image as well as the history of changes that the crowd has made over time.

# Milestone 1: Deliverable 2 Item Locations

Raw data

- Raw data can be found in the /src/static/data folder of this project.
- For the purposes of this project, the raw data is a set of images.

Sample input/output for QC

- Input data is found in our /src/static/data folder, as mentioned above.
- Output data (where votes are tallied) in local storage.

Sample input/output for aggregation

- Both sample input and output data can be found in the /src/static/docs folder.
- In this folder, there is a sample input and output image.

Code for QC

- Code for the QC module can be found in the /src/templates and /src/static folders.

Code for aggregation

- Code for the aggregation module can be found in the /src/aggregation.py script.
