import axios from "axios";
import { TeamsActivityHandler, TurnContext } from "botbuilder";

export class TeamsBot extends TeamsActivityHandler {
  lastQuery: {
    query: string,
    ans: string
  }[] = [];
  aadObjectId:string;
  apiUrl = `https://f58c-2409-40e3-189-aaab-d136-473c-84fc-a11c.ngrok-free.app/query`;
  constructor() {
    super();
    this.onMessage(async (context, next) => {
      const removedMentionText = TurnContext.removeRecipientMention(context.activity);
      const txt = removedMentionText.toLowerCase().replace(/\n|\r/g, "").trim();
      await this.showTypingIndicator(context);
      try {
        const apiResponse = await this.callExternalApi(txt);
        await context.sendActivity(`${apiResponse}`);
      } catch (error) {
        console.error('Error calling API:', error);
        await context.sendActivity('Sorry, there was an error connecting to the API.');
      }
      await next();
    });

    this.onMembersAdded(async (context, next) => {
      const membersAdded = context.activity.membersAdded;
      this.aadObjectId=membersAdded[0]?.aadObjectId;
      console.log(this.aadObjectId);
      console.log(membersAdded[0]);
      for (let cnt = 0; cnt < membersAdded.length; cnt++) {
        if (membersAdded[cnt].id) {
          await context.sendActivity(
            `Hi there! You are connected to RecallIQ.`
          );
          break;
        }
      }
      await next();
    });
  }
  private async callExternalApi(query: string): Promise<string> {
    try {
      let data = this.getRequestPayload(query);
      console.log(data);
      const response = await axios.post(this.apiUrl, data);
      this.maintainContext(query, response);
      return response.data;
    } catch (error) {
      throw new Error(`API request failed: ${error.message}`);
    }
  }
  private maintainContext(query: string, response: axios.AxiosResponse<any, any>) {
    this.lastQuery.push({ query, ans: response.data });
  }

  private getRequestPayload(query: string) {
    return {
      history: JSON.parse(JSON.stringify(this.lastQuery)),
      question: query,
      userId: this.aadObjectId
    };
  }

  private async showTypingIndicator(context: TurnContext) {
    const typingInterval = setInterval(async () => {
      await context.sendActivity({ type: 'typing' });
    }, 1000); // Send typing indicator every second
    await new Promise(resolve => setTimeout(resolve, 3000));
    clearInterval(typingInterval);
  }
}
