import { Page } from '@/components/Page';
import FileUpload from '@/components/FileUpload';

export default function UploadPage() {
  return (
    <Page
      title="Upload"
      subtitle="Upload your documents to your knowledge base"
    >
      <FileUpload />
    </Page>
  );
}
